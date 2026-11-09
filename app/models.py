"""
Data model + JSON persistence.

- Task — single task (text, description, images, time tracking, paused state).
- Stats — daily total seconds, used to compute today's total and streak.
- Store — top-level container, knows how to load / save / migrate.

Where the data lives:
- built .exe  -> %APPDATA%\\FocusApp\\  (survives rebuilds and moving the .exe)
- from source -> repo root              (keeps dev data apart from real data)

Older builds kept the data next to the .exe; `Store.load()` copies it over
on first launch and leaves the originals untouched.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import date, timedelta
from typing import Optional

log = logging.getLogger(__name__)

APP_DIR_NAME = "FocusApp"
DATA_FILE = "focus_tasks.json"
IMAGES_DIR = "focus_images"


# --- Path helpers ---------------------------------------------------------

def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_base_dir() -> str:
    """Directory next to the .exe (or repo root in dev)."""
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def data_dir() -> str:
    """Directory holding the user's data. Created on demand."""
    if is_frozen():
        root = os.environ.get("APPDATA") or os.path.expanduser("~")
        d = os.path.join(root, APP_DIR_NAME)
    else:
        d = app_base_dir()
    os.makedirs(d, exist_ok=True)
    return d


def data_path() -> str:
    return os.path.join(data_dir(), DATA_FILE)


def images_dir() -> str:
    d = os.path.join(data_dir(), IMAGES_DIR)
    os.makedirs(d, exist_ok=True)
    return d


def log_path() -> str:
    return os.path.join(data_dir(), "focus.log")


# --- Image files ------------------------------------------------------------

def _same_path(a: str, b: str) -> bool:
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def is_managed_image(path: str) -> bool:
    """True if the file sits in our own images folder (so we own its lifetime)."""
    return _same_path(os.path.dirname(path), images_dir())


def import_image(src: str) -> Optional[str]:
    """Copy an image into the images folder and return the new path.

    Attachments used to point at the original file, so moving or deleting it
    broke the task. Files already in the images folder are returned as is.
    """
    if is_managed_image(src):
        return src
    ext = os.path.splitext(src)[1].lower() or ".png"
    dst = os.path.join(images_dir(), f"{uuid.uuid4().hex[:12]}{ext}")
    try:
        shutil.copy2(src, dst)
    except OSError:
        log.exception("Could not import image %s", src)
        return None
    return dst


def remove_image_file(path: str) -> None:
    """Delete an attachment from disk — only if it lives in our images folder."""
    if not is_managed_image(path):
        return
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    except OSError:
        log.exception("Could not delete image %s", path)


def _image_to_stored(path: str) -> str:
    """Managed images are stored by bare file name so the data folder can move."""
    return os.path.basename(path) if is_managed_image(path) else path


def _image_from_stored(stored: str) -> str:
    if not os.path.isabs(stored):
        return os.path.join(images_dir(), stored)
    if is_managed_image(stored):
        return stored
    # Absolute path written by an older version. If it pointed into that
    # version's images folder (migrated, or since moved), use our copy.
    from_old_images_dir = os.path.basename(os.path.dirname(stored)).lower() == IMAGES_DIR
    if from_old_images_dir or not os.path.exists(stored):
        candidate = os.path.join(images_dir(), os.path.basename(stored))
        if os.path.exists(candidate):
            return candidate
    return stored


# --- Lenient parsing --------------------------------------------------------

def _as_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_str(value, default: str = "") -> str:
    return value if isinstance(value, str) else default


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
        d = asdict(self)
        d["images"] = [_image_to_stored(p) for p in self.images]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        images = d.get("images")
        return cls(
            id=_as_str(d.get("id")) or str(uuid.uuid4()),
            text=_as_str(d.get("text")),
            description=_as_str(d.get("description")),
            images=[_image_from_stored(p) for p in images if isinstance(p, str) and p]
            if isinstance(images, list) else [],
            time_spent=max(0, _as_int(d.get("time_spent"))),
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
        daily = d.get("daily")
        return cls(
            daily={str(k): _as_int(v) for k, v in daily.items()}
            if isinstance(daily, dict) else {},
            last_active_date=_as_str(d.get("last_active_date")),
        )


# --- Settings ------------------------------------------------------------

@dataclass
class Settings:
    opacity: float = 0.90
    pomodoro_work: int = 25 * 60
    pomodoro_break: int = 5 * 60
    focus_bg: str = "#DC2626"   # designer's default red
    focus_fg: str = "#FFFFFF"
    tray_hint_shown: bool = False   # "still running in the tray" shown once

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Settings":
        defaults = cls()
        return cls(
            opacity=_as_float(d.get("opacity"), defaults.opacity),
            # A zero-length phase would flip work/break every second.
            pomodoro_work=max(60, _as_int(d.get("pomodoro_work"), defaults.pomodoro_work)),
            pomodoro_break=max(60, _as_int(d.get("pomodoro_break"), defaults.pomodoro_break)),
            focus_bg=_as_str(d.get("focus_bg"), defaults.focus_bg),
            focus_fg=_as_str(d.get("focus_fg"), defaults.focus_fg),
            tray_hint_shown=bool(d.get("tray_hint_shown", False)),
        )


# --- Store --------------------------------------------------------------

def _migrate_legacy_data() -> None:
    """Copy data that older builds kept next to the .exe into the data folder."""
    old_dir = app_base_dir()
    new_dir = data_dir()
    if _same_path(old_dir, new_dir):
        return
    old_file = os.path.join(old_dir, DATA_FILE)
    new_file = os.path.join(new_dir, DATA_FILE)
    if os.path.exists(new_file) or not os.path.exists(old_file):
        return
    try:
        old_images = os.path.join(old_dir, IMAGES_DIR)
        if os.path.isdir(old_images):
            shutil.copytree(old_images, images_dir(), dirs_exist_ok=True)
        # The data file goes last: its presence marks the migration as done.
        shutil.copy2(old_file, new_file)
        log.info("Migrated data from %s to %s", old_dir, new_dir)
    except OSError:
        log.exception("Could not migrate data from %s", old_dir)


@dataclass
class Store:
    tasks: list[Task] = field(default_factory=list)
    settings: Settings = field(default_factory=Settings)
    stats: Stats = field(default_factory=Stats)
    # Set by load() when the data file was unreadable; shown to the user once.
    load_warning: str = field(default="", compare=False)

    @classmethod
    def _read(cls, path: str) -> Optional["Store"]:
        """Parse a data file. Returns None if it is missing or unreadable."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            if not isinstance(d, dict):
                raise ValueError("top-level JSON value is not an object")
            tasks = d.get("tasks")
            settings = d.get("settings")
            stats = d.get("stats")
            return cls(
                tasks=[Task.from_dict(t) for t in tasks if isinstance(t, dict)]
                if isinstance(tasks, list) else [],
                settings=Settings.from_dict(settings if isinstance(settings, dict) else {}),
                stats=Stats.from_dict(stats if isinstance(stats, dict) else {}),
            )
        except FileNotFoundError:
            return None
        except (OSError, ValueError):  # JSONDecodeError is a ValueError
            log.exception("Could not read %s", path)
            return None

    @classmethod
    def load(cls) -> "Store":
        _migrate_legacy_data()
        path = data_path()
        backup = path + ".bak"
        if not os.path.exists(path):
            return cls()

        store = cls._read(path)
        if store is not None:
            # Known-good copy, refreshed once per launch.
            try:
                shutil.copy2(path, backup)
            except OSError:
                log.exception("Could not refresh backup %s", backup)
            return store

        # Unreadable: move it aside instead of letting the next save erase it.
        kept = f"{path}.corrupt-{time.strftime('%Y%m%d-%H%M%S')}"
        try:
            os.replace(path, kept)
        except OSError:
            log.exception("Could not set aside unreadable data file")
            kept = path
        restored = cls._read(backup)
        store = restored if restored is not None else cls()
        store.load_warning = (
            "The data file could not be read"
            + (", so the last backup was restored." if restored is not None
               else " and there was no backup, so the task list starts empty.")
            + f"\n\nThe unreadable file was kept as:\n{kept}"
        )
        return store

    def save(self) -> bool:
        """Write the data file atomically. Returns False if it could not be written."""
        path = data_path()
        tmp = path + ".tmp"
        d = {
            "tasks": [t.to_dict() for t in self.tasks],
            "settings": self.settings.to_dict(),
            "stats": self.stats.to_dict(),
        }
        try:
            # Write a sibling file first: a crash mid-write must never leave
            # a truncated focus_tasks.json behind.
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
            return True
        except OSError:
            log.exception("Could not save %s", path)
            return False

    def find(self, task_id: str) -> Optional[Task]:
        return next((t for t in self.tasks if t.id == task_id), None)

    def active_count(self) -> int:
        return sum(1 for t in self.tasks if not t.done)
