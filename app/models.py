"""
Data model + JSON persistence.

- Task — single task (text, description, images, time tracking, paused state).
- Stats — daily total seconds, used to compute today's total and streak.
- Store — top-level container, knows how to load / save / migrate.

Compatible with the old focus_tasks.json format (we add new fields with defaults).
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from dataclasses import dataclass, field, asdict
from datetime import date, timedelta
from typing import Optional


# --- Path helpers ---------------------------------------------------------

def app_base_dir() -> str:
    """Directory next to the .exe (or repo root in dev)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def data_path() -> str:
    return os.path.join(app_base_dir(), "focus_tasks.json")


def images_dir() -> str:
    d = os.path.join(app_base_dir(), "focus_images")
    os.makedirs(d, exist_ok=True)
    return d


# --- Task ----------------------------------------------------------------

@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    description: str = ""
    images: list[str] = field(default_factory=list)
    time_spent: int = 0          # accumulated seconds across all sessions
    done: bool = False
    paused: bool = False         # NEW in v2 — independent of `done` / running

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        return cls(
            id=d.get("id") or str(uuid.uuid4()),
            text=d.get("text", ""),
            description=d.get("description", ""),
            images=list(d.get("images", [])),
            time_spent=int(d.get("time_spent", 0)),
            done=bool(d.get("done", False)),
            paused=bool(d.get("paused", False)),
        )


# --- Stats ---------------------------------------------------------------

@dataclass
class Stats:
    """Per-day focus seconds, used for Today/Streak in the footer."""
    daily: dict[str, int] = field(default_factory=dict)
    last_active_date: str = ""

    @staticmethod
    def _today_iso() -> str:
        return date.today().isoformat()

    def add_seconds(self, seconds: int) -> None:
        if seconds <= 0:
            return
        d = self._today_iso()
        self.daily[d] = self.daily.get(d, 0) + int(seconds)
        self.last_active_date = d

    def today_seconds(self) -> int:
        return self.daily.get(self._today_iso(), 0)

    def streak_days(self) -> int:
        """Consecutive days (including today) with at least 1 sec of focus."""
        if not self.daily:
            return 0
        today = date.today()
        count = 0
        cursor = today
        # Streak counts today only if it has activity, else starts from yesterday.
        if self.daily.get(cursor.isoformat(), 0) <= 0:
            cursor -= timedelta(days=1)
        while self.daily.get(cursor.isoformat(), 0) > 0:
            count += 1
            cursor -= timedelta(days=1)
        return count

    def to_dict(self) -> dict:
        return {"daily": dict(self.daily), "last_active_date": self.last_active_date}

    @classmethod
    def from_dict(cls, d: dict) -> "Stats":
        return cls(
            daily={k: int(v) for k, v in (d.get("daily") or {}).items()},
            last_active_date=d.get("last_active_date", ""),
        )


# --- Settings ------------------------------------------------------------

@dataclass
class Settings:
    opacity: float = 0.90
    pomodoro_work: int = 25 * 60
    pomodoro_break: int = 5 * 60
    focus_bg: str = "#DC2626"   # designer's default red
    focus_fg: str = "#FFFFFF"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Settings":
        defaults = cls()
        return cls(
            opacity=float(d.get("opacity", defaults.opacity)),
            pomodoro_work=int(d.get("pomodoro_work", defaults.pomodoro_work)),
            pomodoro_break=int(d.get("pomodoro_break", defaults.pomodoro_break)),
            focus_bg=d.get("focus_bg", defaults.focus_bg),
            focus_fg=d.get("focus_fg", defaults.focus_fg),
        )


# --- Store --------------------------------------------------------------

@dataclass
class Store:
    tasks: list[Task] = field(default_factory=list)
    settings: Settings = field(default_factory=Settings)
    stats: Stats = field(default_factory=Stats)

    @classmethod
    def load(cls) -> "Store":
        path = data_path()
        if not os.path.exists(path):
            return cls()
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, json.JSONDecodeError):
            return cls()
        return cls(
            tasks=[Task.from_dict(t) for t in d.get("tasks", [])],
            settings=Settings.from_dict(d.get("settings", {})),
            stats=Stats.from_dict(d.get("stats", {})),
        )

    def save(self) -> None:
        path = data_path()
        d = {
            "tasks": [t.to_dict() for t in self.tasks],
            "settings": self.settings.to_dict(),
            "stats": self.stats.to_dict(),
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def find(self, task_id: str) -> Optional[Task]:
        return next((t for t in self.tasks if t.id == task_id), None)

    def active_count(self) -> int:
        return sum(1 for t in self.tasks if not t.done)
