"""
Focus App - Stay focused on your current task.
Displays current task in large text, always on top.
Two modes: Setup (manage tasks) and Focus (display task).
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import colorchooser, filedialog
import json
import uuid
import time
import os
import sys
import re
import math
import ctypes
import ctypes.wintypes
import threading
import webbrowser

from PIL import Image, ImageTk, ImageGrab

try:
    import windnd
    HAS_DND = True
except ImportError:
    HAS_DND = False


# --- Constants ---
DEFAULT_COLOR = "#2D2D2D"
DEFAULT_TEXT_COLOR = "#FFFFFF"
POMODORO_WORK = 25 * 60
POMODORO_BREAK = 5 * 60
DATA_FILE = "focus_tasks.json"
HOTKEY_STOP = 1
HOTKEY_DONE = 2
HOTKEY_PAUSE_TIMER = 3

# Style — neutral gray palette
S_BG = "#1A1A1A"
S_FG = "#D4D4D4"
S_ACCENT = "#A0A0A0"
S_ACCENT_HOVER = "#BCBCBC"
S_SURFACE = "#2A2A2A"
S_GREEN = "#A6E3A1"
S_RED = "#F38BA8"
S_YELLOW = "#F9E2AF"
S_DIM = "#707070"
S_ACTIVE = "#383838"


def get_data_path():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, DATA_FILE)


def get_images_dir():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(base, "focus_images")
    os.makedirs(d, exist_ok=True)
    return d


def format_time(seconds):
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def get_contrast_text_color(hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#FFFFFF" if luminance < 0.5 else "#1A1A1A"


class Task:
    def __init__(self, text="", done=False, time_spent=0, task_id=None,
                 description="", images=None):
        self.id = task_id or str(uuid.uuid4())
        self.text = text
        self.done = done
        self.time_spent = time_spent
        self.description = description
        self.images = images or []

    def to_dict(self):
        return {
            "id": self.id, "text": self.text, "done": self.done,
            "time_spent": self.time_spent, "description": self.description,
            "images": self.images,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            text=d.get("text", ""), done=d.get("done", False),
            time_spent=d.get("time_spent", 0), task_id=d.get("id"),
            description=d.get("description", ""), images=d.get("images", []),
        )


class FocusApp:
    def __init__(self):
        self.tasks: list[Task] = []
        self.settings = {
            "opacity": 0.90,
            "pomodoro_work": POMODORO_WORK,
            "pomodoro_break": POMODORO_BREAK,
            "focus_bg": DEFAULT_COLOR,
            "focus_fg": DEFAULT_TEXT_COLOR,
            "app_bg": S_BG,
            "app_fg": S_FG,
            "app_accent": S_ACCENT,
            "app_surface": S_SURFACE,
        }
        self.active_task: Task | None = None
        self.focus_window: FocusWindow | None = None
        self.expanded_task_id: str | None = None
        self._thumb_cache: dict = {}
        self._desc_widget: ctk.CTkTextbox | None = None
        self._desc_task_id: str | None = None
        self._highlight_timer = None
        self._task_cards: dict = {}
        self._empty_label = None
        self.timer_running = False
        self.timer_paused = False
        self.timer_seconds = 0
        self.is_break = False
        self.tracking_start = 0

        self.load_data()
        self._apply_app_palette()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.withdraw()  # hide until UI is fully built — kills startup flash
        self.root.title("Focus App")
        self.root.geometry("720x650")
        self.root.minsize(600, 400)
        self.root.configure(fg_color=S_BG)

        try:
            self.root.iconbitmap(default="")
        except Exception:
            pass

        self._color_settings_win = None
        self.setup_ui()
        self.register_hotkeys()
        self.root.bind("<Control-p>", lambda e: self._toggle_color_settings())
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.update_idletasks()
        self.root.deiconify()  # show fully-rendered window in one go
        self.root.mainloop()

    # --- Data Persistence ---
    def load_data(self):
        path = get_data_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
                self.settings.update(data.get("settings", {}))
            except (json.JSONDecodeError, KeyError):
                self.tasks = []

    def save_data(self):
        path = get_data_path()
        data = {"tasks": [t.to_dict() for t in self.tasks], "settings": self.settings}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _apply_app_palette(self):
        global S_BG, S_FG, S_ACCENT, S_ACCENT_HOVER, S_SURFACE
        S_BG = self.settings.get("app_bg", S_BG)
        S_FG = self.settings.get("app_fg", S_FG)
        S_ACCENT = self.settings.get("app_accent", S_ACCENT)
        S_SURFACE = self.settings.get("app_surface", S_SURFACE)
        r, g, b = int(S_ACCENT[1:3], 16), int(S_ACCENT[3:5], 16), int(S_ACCENT[5:7], 16)
        S_ACCENT_HOVER = f"#{min(255, r+28):02x}{min(255, g+28):02x}{min(255, b+28):02x}"

    # --- Setup UI ---
    def setup_ui(self):
        # Header
        header = ctk.CTkFrame(self.root, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(10, 0))

        ctk.CTkLabel(
            header, text="FOCUS APP", font=("Segoe UI", 22, "bold"),
            text_color=S_ACCENT
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="Ctrl+Shift+S: Stop  |  Ctrl+Shift+D: Done  |  Ctrl+Shift+P: Pause",
            font=("Segoe UI", 9), text_color=S_DIM
        ).pack(side="right", pady=(8, 0))

        # Settings row
        settings = ctk.CTkFrame(self.root, fg_color="transparent")
        settings.pack(fill="x", padx=20, pady=(8, 0))

        ctk.CTkLabel(settings, text="Opacity:", font=("Segoe UI", 10),
                     text_color=S_FG).pack(side="left")

        self.opacity_var = ctk.DoubleVar(value=self.settings["opacity"])
        ctk.CTkSlider(
            settings, from_=0.3, to=1.0, variable=self.opacity_var,
            command=self._on_opacity_change, width=120,
            fg_color=S_SURFACE, progress_color=S_ACCENT, button_color=S_ACCENT,
            button_hover_color=S_ACCENT_HOVER
        ).pack(side="left", padx=(5, 3))

        self.opacity_label = ctk.CTkLabel(
            settings, text=f"{self.settings['opacity']:.0%}",
            font=("Segoe UI", 10), text_color=S_FG, width=35
        )
        self.opacity_label.pack(side="left", padx=(0, 15))

        ctk.CTkLabel(settings, text="Work:", font=("Segoe UI", 10),
                     text_color=S_FG).pack(side="left")
        self.work_min_var = ctk.StringVar(value=str(self.settings["pomodoro_work"] // 60))
        work_entry = ctk.CTkEntry(
            settings, textvariable=self.work_min_var, width=45, height=28,
            font=("Segoe UI", 10), fg_color=S_SURFACE, text_color=S_FG,
            border_color=S_SURFACE, corner_radius=4
        )
        work_entry.pack(side="left", padx=2)
        work_entry.bind("<Return>", lambda e: self._on_pomodoro_change())
        work_entry.bind("<FocusOut>", lambda e: self._on_pomodoro_change())

        ctk.CTkLabel(settings, text="min  Break:", font=("Segoe UI", 10),
                     text_color=S_FG).pack(side="left")
        self.break_min_var = ctk.StringVar(value=str(self.settings["pomodoro_break"] // 60))
        break_entry = ctk.CTkEntry(
            settings, textvariable=self.break_min_var, width=45, height=28,
            font=("Segoe UI", 10), fg_color=S_SURFACE, text_color=S_FG,
            border_color=S_SURFACE, corner_radius=4
        )
        break_entry.pack(side="left", padx=2)
        break_entry.bind("<Return>", lambda e: self._on_pomodoro_change())
        break_entry.bind("<FocusOut>", lambda e: self._on_pomodoro_change())

        ctk.CTkLabel(settings, text="min", font=("Segoe UI", 10),
                     text_color=S_FG).pack(side="left", padx=(2, 0))

        # Focus color row
        colors = ctk.CTkFrame(self.root, fg_color="transparent")
        colors.pack(fill="x", padx=20, pady=(6, 0))

        ctk.CTkLabel(colors, text="Focus BG:", font=("Segoe UI", 10),
                     text_color=S_FG).pack(side="left")
        self.bg_color_btn = ctk.CTkButton(
            colors, text="", width=30, height=24, corner_radius=4,
            fg_color=self.settings["focus_bg"],
            hover_color=self.settings["focus_bg"],
            command=self._pick_bg_color
        )
        self.bg_color_btn.pack(side="left", padx=(4, 16))

        ctk.CTkLabel(colors, text="Focus Text:", font=("Segoe UI", 10),
                     text_color=S_FG).pack(side="left")
        self.fg_color_btn = ctk.CTkButton(
            colors, text="", width=30, height=24, corner_radius=4,
            fg_color=self.settings["focus_fg"],
            hover_color=self.settings["focus_fg"],
            command=self._pick_fg_color
        )
        self.fg_color_btn.pack(side="left", padx=(4, 0))

        # Separator
        ctk.CTkFrame(self.root, fg_color=S_SURFACE, height=1).pack(
            fill="x", padx=20, pady=6)

        # Add task bar
        add_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        add_frame.pack(fill="x", padx=20, pady=(2, 0))

        self.new_task_var = ctk.StringVar()
        entry = ctk.CTkEntry(
            add_frame, textvariable=self.new_task_var,
            font=("Segoe UI", 13), fg_color=S_SURFACE, text_color=S_FG,
            border_color=S_SURFACE, placeholder_text="New task...",
            height=38, corner_radius=8
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        entry.bind("<Return>", lambda e: self.add_task())

        ctk.CTkButton(
            add_frame, text="+ ADD TASK", font=("Segoe UI", 12, "bold"),
            fg_color=S_ACCENT, text_color="#1E1E2E", hover_color=S_ACCENT_HOVER,
            corner_radius=8, height=38, command=self.add_task
        ).pack(side="right")

        # Scrollable task list
        self.task_list_frame = ctk.CTkScrollableFrame(
            self.root, fg_color="transparent",
            scrollbar_button_color=S_SURFACE,
            scrollbar_button_hover_color=S_ACTIVE
        )
        self.task_list_frame.pack(fill="both", expand=True, padx=20, pady=(6, 10))

        self.refresh_task_list()

    # --- Task list ---
    def toggle_expand(self, task_id):
        prev_expanded = self.expanded_task_id
        if prev_expanded == task_id:
            self.expanded_task_id = None
        else:
            self.expanded_task_id = task_id
        # Incrementally refresh only the affected cards
        if prev_expanded and prev_expanded != task_id:
            self._refresh_one_card(prev_expanded)
        self._refresh_one_card(task_id)

    def _show_or_hide_empty(self):
        if not self.tasks:
            if self._empty_label is None:
                self._empty_label = ctk.CTkLabel(
                    self.task_list_frame, text="No tasks yet. Add one above!",
                    font=("Segoe UI", 13), text_color=S_DIM
                )
                self._empty_label.pack(pady=40)
        elif self._empty_label is not None:
            self._empty_label.destroy()
            self._empty_label = None

    def _next_card_widget(self, task_id):
        """Return the card widget that follows task_id in self.tasks order."""
        idx = next((i for i, t in enumerate(self.tasks) if t.id == task_id), None)
        if idx is None:
            return None
        for j in range(idx + 1, len(self.tasks)):
            w = self._task_cards.get(self.tasks[j].id)
            if w is not None:
                return w
        return None

    def _refresh_one_card(self, task_id):
        """Rebuild a single task card in place — avoids full list redraw."""
        if self._desc_task_id == task_id:
            self._save_description()
            self._desc_widget = None
            self._desc_task_id = None

        old = self._task_cards.pop(task_id, None)
        task = next((t for t in self.tasks if t.id == task_id), None)

        if task is None:
            # Task was deleted — just remove its card
            if old is not None:
                old.destroy()
            self._show_or_hide_empty()
            return

        before = self._next_card_widget(task_id) if old is None else None
        if old is not None:
            # Preserve position by placing new card before the next one
            before = self._next_card_widget(task_id)
            old.destroy()

        self._build_card(task, before=before)
        self._show_or_hide_empty()

    def refresh_task_list(self):
        """Full rebuild — used on first paint and rare structural changes."""
        self._save_description()
        self._desc_widget = None
        self._desc_task_id = None

        for card in self._task_cards.values():
            card.destroy()
        self._task_cards.clear()

        self._show_or_hide_empty()
        for task in self.tasks:
            self._build_card(task)

    def _build_card(self, task, before=None):
        """Build a single task card and pack it into the list (optionally before another card)."""
        is_active = self.active_task and self.active_task.id == task.id
        is_expanded = self.expanded_task_id == task.id

        # Make sure empty label is gone if we're adding a card
        if self._empty_label is not None:
            self._empty_label.destroy()
            self._empty_label = None

        card = ctk.CTkFrame(
            self.task_list_frame, corner_radius=10,
            fg_color=S_ACTIVE if is_active else S_SURFACE,
            border_width=2,
            border_color=S_ACCENT if is_active else S_SURFACE
        )
        if before is not None:
            card.pack(fill="x", pady=4, before=before)
        else:
            card.pack(fill="x", pady=4)
        self._task_cards[task.id] = card

        # === Header row ===
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(8, 4 if not is_expanded else 4))

        arrow = "\u25BC" if is_expanded else "\u25B6"
        arrow_lbl = ctk.CTkLabel(
            header, text=arrow, font=("Segoe UI", 11), text_color=S_DIM,
            cursor="hand2", width=16
        )
        arrow_lbl.pack(side="left", padx=(0, 6))

        task_font = ("Segoe UI", 14, "bold") if is_active else ("Segoe UI", 14)
        task_fg = S_DIM if task.done else S_FG
        task_text = f"\u2713 {task.text}" if task.done else task.text

        name_lbl = ctk.CTkLabel(
            header, text=task_text, font=task_font,
            text_color=task_fg, anchor="w", cursor="hand2"
        )
        name_lbl.pack(side="left", fill="x", expand=True)

        # Indicators when collapsed
        if not is_expanded:
            ind = []
            if task.description.strip():
                ind.append("\U0001F4DD")
            if task.images:
                ind.append(f"\U0001F4F7{len(task.images)}")
            if ind:
                ctk.CTkLabel(
                    header, text="  ".join(ind), font=("Segoe UI", 10),
                    text_color=S_DIM
                ).pack(side="left", padx=(8, 0))

        # Time
        time_text = format_time(task.time_spent)
        if is_active and self.timer_running:
            time_text += " \u23F1"
        ctk.CTkLabel(
            header, text=time_text, font=("Segoe UI", 10),
            text_color=S_DIM
        ).pack(side="left", padx=(10, 0))

        # Buttons
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")

        if not task.done:
            if is_active:
                ctk.CTkButton(
                    btn_frame, text="STOP", font=("Segoe UI", 11, "bold"),
                    fg_color=S_RED, text_color="#1E1E2E", hover_color="#F5A0B5",
                    corner_radius=6, width=70, height=30, command=self.stop_focus
                ).pack(side="left", padx=2)
            else:
                ctk.CTkButton(
                    btn_frame, text="START", font=("Segoe UI", 11, "bold"),
                    fg_color=S_GREEN, text_color="#1E1E2E", hover_color="#BFE8BB",
                    corner_radius=6, width=70, height=30,
                    command=lambda t=task: self.start_focus(t)
                ).pack(side="left", padx=2)

            ctk.CTkButton(
                btn_frame, text="DONE", font=("Segoe UI", 11, "bold"),
                fg_color=S_YELLOW, text_color="#1E1E2E", hover_color="#FAE9C4",
                corner_radius=6, width=70, height=30,
                command=lambda t=task: self.mark_done(t)
            ).pack(side="left", padx=2)

        if task.done:
            ctk.CTkButton(
                btn_frame, text="\u2715", font=("Segoe UI", 13),
                fg_color=S_RED, text_color="#1E1E2E", hover_color="#F5A0B5",
                corner_radius=6, width=34, height=30,
                command=lambda t=task: self.delete_task(t)
            ).pack(side="left", padx=2)

        # Click to expand
        for w in (arrow_lbl, name_lbl):
            w.bind("<Button-1>", lambda e, tid=task.id: self.toggle_expand(tid))

        # === Expanded section ===
        if is_expanded:
            detail = ctk.CTkFrame(card, fg_color="transparent")
            detail.pack(fill="x", padx=12, pady=(0, 8))

            ctk.CTkFrame(detail, fg_color=S_DIM, height=1).pack(fill="x", pady=(0, 8))

            # Editable name
            name_row = ctk.CTkFrame(detail, fg_color="transparent")
            name_row.pack(fill="x", pady=(0, 6))

            ctk.CTkLabel(
                name_row, text="Name:", font=("Segoe UI", 10, "bold"),
                text_color=S_FG
            ).pack(side="left")

            name_var = ctk.StringVar(value=task.text)
            name_entry = ctk.CTkEntry(
                name_row, textvariable=name_var, font=("Segoe UI", 11),
                fg_color=S_BG, text_color=S_FG, border_color=S_SURFACE,
                corner_radius=6, height=32
            )
            name_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))

            def save_name(e, t=task, var=name_var):
                new = var.get().strip()
                if new and new != t.text:
                    t.text = new
                    self.save_data()
                    self._refresh_one_card(t.id)
            name_entry.bind("<Return>", save_name)
            name_entry.bind("<FocusOut>", save_name)

            # Description textbox
            desc_text = ctk.CTkTextbox(
                detail, font=("Segoe UI", 11), fg_color=S_BG, text_color=S_FG,
                border_color=S_SURFACE, border_width=1,
                corner_radius=8, height=120, wrap="word"
            )
            desc_text.pack(fill="x", pady=(0, 4))
            if task.description:
                desc_text.insert("1.0", task.description)

            self._desc_widget = desc_text
            self._desc_task_id = task.id

            # Tags for auto-links (use internal _textbox)
            tb = desc_text._textbox
            tb.tag_configure("url", foreground="#89DCEB", underline=True)
            tb.tag_bind("url", "<Button-1>",
                        lambda e: self._on_tag_click(e, "url"))
            tb.tag_bind("url", "<Enter>",
                        lambda e: tb.configure(cursor="hand2"))
            tb.tag_bind("url", "<Leave>",
                        lambda e: tb.configure(cursor="xterm"))

            desc_text.bind("<KeyRelease>", lambda e: self._schedule_highlight())
            desc_text.bind("<FocusOut>", lambda e: self._save_description())
            desc_text.bind("<Control-v>", lambda e, t=task: self._on_paste(e, t))

            self._apply_text_tags()

            # DnD
            if HAS_DND:
                def on_drop(files, t=task):
                    img_exts = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
                    added = False
                    for f in files:
                        p = os.fsdecode(f) if isinstance(f, bytes) else str(f)
                        if os.path.splitext(p)[1].lower() in img_exts:
                            t.images.append(p)
                            added = True
                    if added:
                        self._save_description()
                        self.save_data()
                        self._refresh_one_card(t.id)
                windnd.hook_dropfiles(tb, func=on_drop)

            # Image bar
            img_bar = ctk.CTkFrame(detail, fg_color="transparent")
            img_bar.pack(fill="x", pady=(2, 2))

            hints = ["Ctrl+V paste image"]
            if HAS_DND:
                hints.append("Drop files")
            ctk.CTkLabel(
                img_bar, text="  |  ".join(hints),
                font=("Segoe UI", 9), text_color=S_DIM
            ).pack(side="left")

            ctk.CTkButton(
                img_bar, text="+ Image", font=("Segoe UI", 10),
                fg_color=S_ACCENT, text_color="#1E1E2E", hover_color=S_ACCENT_HOVER,
                corner_radius=6, width=80, height=26,
                command=lambda t=task: self._add_image(t)
            ).pack(side="right")

            # Thumbnails
            if task.images:
                thumbs = ctk.CTkFrame(detail, fg_color="transparent")
                thumbs.pack(fill="x", pady=(2, 4))

                for i, img_path in enumerate(task.images):
                    tc = ctk.CTkFrame(thumbs, fg_color=S_BG, corner_radius=6)
                    tc.pack(side="left", padx=(0, 6), pady=2)

                    thumb = self._make_thumbnail(img_path, 80)
                    if thumb:
                        tl = tk.Label(tc, image=thumb, bg=S_BG, cursor="hand2")
                        tl.pack(padx=4, pady=(4, 0))
                        tl.bind("<Button-1>",
                                lambda e, p=img_path: self._open_image_viewer(p))
                    else:
                        ctk.CTkLabel(
                            tc, text="[err]", font=("Segoe UI", 9),
                            text_color=S_RED
                        ).pack(padx=4, pady=4)

                    fname = os.path.basename(img_path)
                    if len(fname) > 14:
                        fname = fname[:11] + "..."

                    bot = ctk.CTkFrame(tc, fg_color="transparent")
                    bot.pack(fill="x", padx=4, pady=(0, 2))

                    ctk.CTkLabel(
                        bot, text=fname, font=("Segoe UI", 8),
                        text_color=S_DIM, anchor="w"
                    ).pack(side="left", fill="x", expand=True)

                    ctk.CTkButton(
                        bot, text="\u2715", font=("Segoe UI", 9),
                        fg_color="transparent", text_color=S_RED,
                        hover_color=S_SURFACE, width=20, height=16,
                        command=lambda t=task, idx=i: self._remove_image(t, idx)
                    ).pack(side="right")

    # --- Task Actions ---
    def add_task(self):
        text = self.new_task_var.get().strip()
        if not text:
            return
        task = Task(text=text)
        self.tasks.append(task)
        self.new_task_var.set("")
        self.save_data()
        self._build_card(task)  # incremental — append the new card

    def mark_done(self, task: Task):
        if self.active_task and self.active_task.id == task.id:
            self.stop_focus()
        task.done = True
        self._delete_task_images(task)
        self.save_data()
        self._refresh_one_card(task.id)

    def delete_task(self, task: Task):
        self._delete_task_images(task)
        task_id = task.id
        self.tasks = [t for t in self.tasks if t.id != task_id]
        self.save_data()
        self._refresh_one_card(task_id)  # detects task is gone → just removes card

    def _delete_task_images(self, task: Task):
        images_dir = get_images_dir()
        for path in task.images:
            norm = os.path.normpath(path)
            if os.path.normpath(images_dir) in norm:
                try:
                    os.remove(norm)
                except OSError:
                    pass
        task.images.clear()

    # --- Description & Auto-links ---
    def _save_description(self):
        if self._desc_widget and self._desc_task_id:
            try:
                content = self._desc_widget.get("1.0", "end-1c")
            except Exception:
                return
            for task in self.tasks:
                if task.id == self._desc_task_id:
                    task.description = content
                    break

    def _schedule_highlight(self):
        if self._highlight_timer:
            self.root.after_cancel(self._highlight_timer)
        self._highlight_timer = self.root.after(300, self._apply_text_tags)

    def _apply_text_tags(self):
        w = self._desc_widget
        if not w:
            return
        try:
            tb = w._textbox
            content = w.get("1.0", "end-1c")
        except Exception:
            return
        tb.tag_remove("url", "1.0", "end")
        for match in re.finditer(r'https?://\S+', content):
            tb.tag_add("url", f"1.0+{match.start()}c", f"1.0+{match.end()}c")

    def _on_tag_click(self, event, tag_name):
        w = self._desc_widget
        if not w:
            return
        tb = w._textbox
        idx = tb.index(f"@{event.x},{event.y}")
        ranges = tb.tag_ranges(tag_name)
        for i in range(0, len(ranges), 2):
            start, end = ranges[i], ranges[i + 1]
            if tb.compare(start, "<=", idx) and tb.compare(idx, "<", end):
                webbrowser.open(tb.get(start, end))
                break

    def _on_paste(self, event, task: Task):
        try:
            img = ImageGrab.grabclipboard()
            if img is not None and hasattr(img, 'save'):
                fname = f"{uuid.uuid4().hex[:12]}.png"
                path = os.path.join(get_images_dir(), fname)
                img.save(path, "PNG")
                task.images.append(path)
                self._save_description()
                self.save_data()
                self._refresh_one_card(task.id)
                return "break"
        except Exception:
            pass
        return None

    # --- Images ---
    def _add_image(self, task: Task):
        paths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                       ("All files", "*.*")]
        )
        if paths:
            task.images.extend(paths)
            self.save_data()
            self._refresh_one_card(task.id)

    def _remove_image(self, task: Task, index: int):
        if 0 <= index < len(task.images):
            task.images.pop(index)
            self.save_data()
            self._refresh_one_card(task.id)

    def _make_thumbnail(self, path: str, size: int = 80):
        try:
            img = Image.open(path)
            img.thumbnail((size, size), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._thumb_cache[path] = photo
            return photo
        except Exception:
            return None

    def _open_image_viewer(self, path: str):
        try:
            img = Image.open(path)
        except Exception:
            return
        viewer = ctk.CTkToplevel(self.root)
        viewer.title(os.path.basename(path))
        viewer.configure(fg_color="#111111")
        viewer.transient(self.root)

        screen_w = viewer.winfo_screenwidth() - 100
        screen_h = viewer.winfo_screenheight() - 100
        iw, ih = img.size
        scale = min(screen_w / iw, screen_h / ih, 1.0)
        if scale < 1.0:
            img = img.resize((int(iw * scale), int(ih * scale)), Image.LANCZOS)

        viewer.geometry(f"{img.size[0] + 20}x{img.size[1] + 20}")
        photo = ImageTk.PhotoImage(img)
        label = tk.Label(viewer, image=photo, bg="#111111")
        label.image = photo
        label.pack(expand=True)
        viewer.bind("<Escape>", lambda e: viewer.destroy())
        viewer.bind("<Button-1>", lambda e: viewer.destroy())

    # --- Focus color pickers (visible in main UI) ---
    def _pick_bg_color(self):
        color = colorchooser.askcolor(initialcolor=self.settings["focus_bg"],
                                       title="Pick focus background color")
        if color[1]:
            self.settings["focus_bg"] = color[1]
            self.bg_color_btn.configure(fg_color=color[1], hover_color=color[1])
            self.save_data()
            if self.focus_window:
                self.focus_window.update_colors(
                    self.settings["focus_bg"], self.settings["focus_fg"])

    def _pick_fg_color(self):
        color = colorchooser.askcolor(initialcolor=self.settings["focus_fg"],
                                       title="Pick focus text color")
        if color[1]:
            self.settings["focus_fg"] = color[1]
            self.fg_color_btn.configure(fg_color=color[1], hover_color=color[1])
            self.save_data()
            if self.focus_window:
                self.focus_window.update_colors(
                    self.settings["focus_bg"], self.settings["focus_fg"])

    # --- App palette (Ctrl+P, hidden dev feature) ---
    def _toggle_color_settings(self):
        if self._color_settings_win and self._color_settings_win.winfo_exists():
            self._color_settings_win.destroy()
            self._color_settings_win = None
            return
        win = ctk.CTkToplevel(self.root)
        win.title("App Palette")
        win.geometry("300x260")
        win.resizable(False, False)
        win.configure(fg_color=S_BG)
        win.attributes("-topmost", True)
        win.transient(self.root)
        self._color_settings_win = win
        self._palette_btns = {}

        ctk.CTkLabel(
            win, text="APP PALETTE", font=("Segoe UI", 14, "bold"),
            text_color=S_FG
        ).pack(pady=(12, 8))

        palette_items = [
            ("Background", "app_bg"),
            ("Text", "app_fg"),
            ("Accent", "app_accent"),
            ("Surface", "app_surface"),
        ]
        for label, key in palette_items:
            row = ctk.CTkFrame(win, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=3)
            ctk.CTkLabel(row, text=f"{label}:", font=("Segoe UI", 11),
                         text_color=S_FG).pack(side="left")
            btn = ctk.CTkButton(
                row, text="", width=40, height=26, corner_radius=4,
                fg_color=self.settings[key], hover_color=self.settings[key],
                command=lambda k=key: self._pick_palette_color(k)
            )
            btn.pack(side="right")
            self._palette_btns[key] = btn

        ctk.CTkLabel(
            win, text="Changes apply on restart",
            font=("Segoe UI", 9), text_color=S_DIM
        ).pack(pady=(10, 4))

    def _pick_palette_color(self, key):
        color = colorchooser.askcolor(initialcolor=self.settings[key],
                                       title=f"Pick {key}")
        if color[1]:
            self.settings[key] = color[1]
            if key in self._palette_btns:
                self._palette_btns[key].configure(
                    fg_color=color[1], hover_color=color[1])
            self._apply_app_palette()
            self.save_data()
            self.root.configure(fg_color=S_BG)
            self.refresh_task_list()

    def _on_opacity_change(self, val):
        self.settings["opacity"] = float(val)
        self.opacity_label.configure(text=f"{float(val):.0%}")
        self.save_data()
        if self.focus_window:
            self.focus_window.set_opacity(float(val))

    def _on_pomodoro_change(self):
        try:
            self.settings["pomodoro_work"] = int(self.work_min_var.get()) * 60
            self.settings["pomodoro_break"] = int(self.break_min_var.get()) * 60
            self.save_data()
        except (ValueError, Exception):
            pass

    # --- Focus Mode ---
    def start_focus(self, task: Task):
        prev_active_id = self.active_task.id if self.active_task else None
        if self.active_task:
            self.stop_focus()
        self.active_task = task
        self.timer_running = True
        self.timer_paused = False
        self.is_break = False
        self.timer_seconds = self.settings["pomodoro_work"]
        self.tracking_start = time.time()

        self.focus_window = FocusWindow(
            self.root, task,
            bg_color=self.settings["focus_bg"],
            fg_color=self.settings["focus_fg"],
            opacity=self.settings["opacity"],
            on_stop=self.stop_focus,
            on_done=lambda: self.mark_done(task),
            on_pause=self.toggle_pause
        )
        # Incremental: only the new active task changed (prev was already updated by stop_focus)
        self._refresh_one_card(task.id)
        if prev_active_id and prev_active_id != task.id:
            self._refresh_one_card(prev_active_id)
        self._tick()

    def stop_focus(self):
        prev_active_id = self.active_task.id if self.active_task else None
        if self.active_task and self.tracking_start:
            elapsed = time.time() - self.tracking_start
            self.active_task.time_spent += int(elapsed)
            self.tracking_start = 0
        self.active_task = None
        self.timer_running = False
        self.timer_paused = False
        if self.focus_window:
            self.focus_window.close()
            self.focus_window = None
        self.save_data()
        if prev_active_id:
            self._refresh_one_card(prev_active_id)

    def _tick(self):
        if not self.timer_running or not self.focus_window:
            return
        if not self.timer_paused:
            self.timer_seconds -= 1
            if self.active_task and self.tracking_start and not self.is_break:
                elapsed = time.time() - self.tracking_start
                self.focus_window.update_total_time(
                    self.active_task.time_spent + int(elapsed))
            if self.timer_seconds <= 0:
                if self.is_break:
                    self.is_break = False
                    self.timer_seconds = self.settings["pomodoro_work"]
                    self.focus_window.set_phase("WORK")
                    self.tracking_start = time.time()
                else:
                    if self.active_task and self.tracking_start:
                        elapsed = time.time() - self.tracking_start
                        self.active_task.time_spent += int(elapsed)
                        self.tracking_start = 0
                    self.save_data()
                    self.is_break = True
                    self.timer_seconds = self.settings["pomodoro_break"]
                    self.focus_window.set_phase("BREAK")
                    self.focus_window.flash_notify()
        self.focus_window.update_timer(
            self.timer_seconds, self.is_break, self.timer_paused)
        self.root.after(1000, self._tick)

    def toggle_pause(self):
        if self.timer_running:
            self.timer_paused = not self.timer_paused
            if self.timer_paused and self.tracking_start and not self.is_break:
                elapsed = time.time() - self.tracking_start
                self.active_task.time_spent += int(elapsed)
                self.tracking_start = 0
            elif not self.timer_paused and not self.is_break:
                self.tracking_start = time.time()

    # --- Global Hotkeys ---
    def register_hotkeys(self):
        self._hotkey_thread = threading.Thread(target=self._hotkey_listener, daemon=True)
        self._hotkey_thread.start()

    def _hotkey_listener(self):
        user32 = ctypes.windll.user32
        MOD = 0x0002 | 0x0004 | 0x4000  # CTRL + SHIFT + NOREPEAT
        user32.RegisterHotKey(None, HOTKEY_STOP, MOD, 0x53)
        user32.RegisterHotKey(None, HOTKEY_DONE, MOD, 0x44)
        user32.RegisterHotKey(None, HOTKEY_PAUSE_TIMER, MOD, 0x50)

        msg = ctypes.wintypes.MSG()
        while True:
            if user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == 0x0312:
                    hid = msg.wParam
                    if hid == HOTKEY_STOP:
                        self.root.after(0, self.stop_focus)
                    elif hid == HOTKEY_DONE:
                        if self.active_task:
                            t = self.active_task
                            self.root.after(0, lambda: self.mark_done(t))
                    elif hid == HOTKEY_PAUSE_TIMER:
                        self.root.after(0, self.toggle_pause)

    def on_close(self):
        if self.active_task and self.tracking_start:
            elapsed = time.time() - self.tracking_start
            self.active_task.time_spent += int(elapsed)
        self._save_description()
        self.save_data()
        if self.focus_window:
            self.focus_window.close()
        try:
            user32 = ctypes.windll.user32
            user32.UnregisterHotKey(None, HOTKEY_STOP)
            user32.UnregisterHotKey(None, HOTKEY_DONE)
            user32.UnregisterHotKey(None, HOTKEY_PAUSE_TIMER)
        except Exception:
            pass
        self.root.destroy()


class FocusWindow:
    """Always-on-top focus overlay with rounded corners and gradient."""

    TRANS_KEY = "#000001"
    RADIUS = 18

    def __init__(self, parent, task: Task, bg_color: str, fg_color: str,
                 opacity: float, on_stop=None, on_done=None, on_pause=None):
        self.task = task
        self.on_stop = on_stop
        self.on_done = on_done
        self.on_pause = on_pause
        self.bg_color = bg_color
        self.text_color = fg_color

        self.win = tk.Toplevel(parent)
        self.win.title("Focus")
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", opacity)
        self.win.configure(bg=self.TRANS_KEY)
        self.win.wm_attributes("-transparentcolor", self.TRANS_KEY)

        screen_w = self.win.winfo_screenwidth()
        screen_h = self.win.winfo_screenheight()
        self._w, self._h = 500, 210
        self.win.geometry(
            f"{self._w}x{self._h}+{screen_w - self._w - 20}+{screen_h - self._h - 60}")

        self._drag_data = {"x": 0, "y": 0}

        # Canvas for rounded gradient background
        self.canvas = tk.Canvas(
            self.win, highlightthickness=0, bg=self.TRANS_KEY,
            width=self._w, height=self._h)
        self.canvas.pack(fill="both", expand=True)

        self._draw_bg()
        self._build_ui()

        # Drag bindings (exclude pause label and buttons)
        for w in [self.canvas, self.top_row, self.phase_label,
                  self.task_label, self.bottom_row,
                  self.timer_label, self.total_time_label]:
            w.bind("<Button-1>", self._on_drag_start)
            w.bind("<B1-Motion>", self._on_drag_motion)

    # --- Color helpers ---
    def _hex_to_rgb(self, hex_color):
        h = hex_color.lstrip('#')
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    def _lighten_rgb(self, hex_color, amount=0.12):
        r, g, b = self._hex_to_rgb(hex_color)
        return (min(255, int(r + (255 - r) * amount)),
                min(255, int(g + (255 - g) * amount)),
                min(255, int(b + (255 - b) * amount)))

    def _gradient_at(self, y_ratio):
        """Return hex color at y_ratio (0=top lighter, 1=bottom base)."""
        c1 = self._lighten_rgb(self.bg_color, 0.12)
        c2 = self._hex_to_rgb(self.bg_color)
        r = int(c1[0] + (c2[0] - c1[0]) * y_ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * y_ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * y_ratio)
        color = f"#{r:02x}{g:02x}{b:02x}"
        return color if color != self.TRANS_KEY else f"#{r:02x}{g:02x}{max(b, 2):02x}"

    # --- Gradient drawing ---
    def _draw_bg(self):
        self.canvas.delete("bg")
        w, h, rad = self._w, self._h, self.RADIUS
        c_top = self._lighten_rgb(self.bg_color, 0.12)
        c_bot = self._hex_to_rgb(self.bg_color)

        for y in range(h):
            ratio = y / max(h - 1, 1)
            cr = int(c_top[0] + (c_bot[0] - c_top[0]) * ratio)
            cg = int(c_top[1] + (c_bot[1] - c_top[1]) * ratio)
            cb = int(c_top[2] + (c_bot[2] - c_top[2]) * ratio)
            color = f"#{cr:02x}{cg:02x}{cb:02x}"
            if color == self.TRANS_KEY:
                color = f"#{cr:02x}{cg:02x}{max(cb, 2):02x}"

            # Horizontal bounds clipped to rounded rectangle
            if y < rad:
                dy = rad - y
                dx = rad - math.sqrt(max(0, rad * rad - dy * dy))
                x1, x2 = int(dx), w - int(dx)
            elif y > h - rad - 1:
                dy = y - (h - rad - 1)
                dx = rad - math.sqrt(max(0, rad * rad - dy * dy))
                x1, x2 = int(dx), w - int(dx)
            else:
                x1, x2 = 0, w

            self.canvas.create_line(x1, y, x2, y, fill=color, tags="bg")

        self.canvas.tag_lower("bg")

    # --- UI ---
    def _build_ui(self):
        fg = self.text_color
        bg_top = self._gradient_at(0.08)
        bg_mid = self._gradient_at(0.40)
        bg_bot = self._gradient_at(0.88)
        pad_x = 18
        cw = self._w - 2 * pad_x

        # Top row
        self.top_row = tk.Frame(self.canvas, bg=bg_top)
        self.canvas.create_window(
            self._w // 2, 14, window=self.top_row, width=cw, anchor="n")

        self.phase_label = tk.Label(
            self.top_row, text="WORK", font=("Segoe UI", 11, "bold"),
            fg=fg, bg=bg_top)
        self.phase_label.pack(side="left")

        ctk.CTkButton(
            self.top_row, text="\u25A0 STOP", font=("Segoe UI", 10, "bold"),
            fg_color=S_RED, text_color="#1E1E2E", hover_color="#F5A0B5",
            corner_radius=6, width=75, height=28, command=self.on_stop
        ).pack(side="right", padx=(4, 0))

        ctk.CTkButton(
            self.top_row, text="\u2713 DONE", font=("Segoe UI", 10, "bold"),
            fg_color=S_GREEN, text_color="#1E1E2E", hover_color="#BFE8BB",
            corner_radius=6, width=75, height=28, command=self.on_done
        ).pack(side="right", padx=(4, 0))

        self.pause_lbl = tk.Label(
            self.top_row, text="\u23F8", font=("Segoe UI", 14),
            fg=fg, bg=bg_top, cursor="hand2")
        self.pause_lbl.pack(side="right", padx=(4, 4))
        self.pause_lbl.bind("<Button-1>", lambda e: self._toggle_pause())

        # Task text
        self.task_label = tk.Label(
            self.canvas, text=self.task.text,
            font=("Segoe UI", 28, "bold"), fg=fg, bg=bg_mid,
            wraplength=cw - 10, justify="left", anchor="w")
        self.canvas.create_window(
            pad_x + 5, 55, window=self.task_label,
            width=cw - 10, anchor="nw")

        # Bottom row
        self.bottom_row = tk.Frame(self.canvas, bg=bg_bot)
        self.canvas.create_window(
            self._w // 2, self._h - 16, window=self.bottom_row,
            width=cw, anchor="s")

        self.timer_label = tk.Label(
            self.bottom_row, text="25:00",
            font=("Consolas", 24, "bold"), fg=fg, bg=bg_bot)
        self.timer_label.pack(side="left")

        self.total_time_label = tk.Label(
            self.bottom_row, text=f"Total: {format_time(self.task.time_spent)}",
            font=("Segoe UI", 11), fg=fg, bg=bg_bot)
        self.total_time_label.pack(side="right")

    def update_timer(self, seconds, is_break, is_paused):
        text = format_time(seconds)
        if is_paused:
            text += "  PAUSED"
        self.timer_label.configure(text=text)
        self.timer_label.configure(
            fg=S_GREEN if is_break else self.text_color)

    def update_total_time(self, total_seconds):
        self.total_time_label.configure(text=f"Total: {format_time(total_seconds)}")

    def update_colors(self, bg_color, fg_color):
        self.bg_color = bg_color
        self.text_color = fg_color
        self._draw_bg()
        bg_top = self._gradient_at(0.08)
        bg_mid = self._gradient_at(0.40)
        bg_bot = self._gradient_at(0.88)
        self.top_row.configure(bg=bg_top)
        self.phase_label.configure(fg=fg_color, bg=bg_top)
        self.pause_lbl.configure(fg=fg_color, bg=bg_top)
        self.task_label.configure(fg=fg_color, bg=bg_mid)
        self.bottom_row.configure(bg=bg_bot)
        self.timer_label.configure(fg=fg_color, bg=bg_bot)
        self.total_time_label.configure(fg=fg_color, bg=bg_bot)

    def set_phase(self, phase):
        self.phase_label.configure(text=phase)

    def set_opacity(self, opacity):
        self.win.attributes("-alpha", opacity)

    def flash_notify(self):
        orig_bg = self.bg_color
        orig_fg = self.text_color

        def flash(count=0):
            if count >= 6:
                self.update_colors(orig_bg, orig_fg)
                return
            c = "#FFFFFF" if count % 2 == 0 else orig_bg
            self.update_colors(c, orig_fg)
            self.win.after(250, lambda: flash(count + 1))
        flash()

    def _toggle_pause(self):
        if self.on_pause:
            self.on_pause()

    def _on_drag_start(self, event):
        self._drag_data["x"] = event.x_root
        self._drag_data["y"] = event.y_root

    def _on_drag_motion(self, event):
        dx = event.x_root - self._drag_data["x"]
        dy = event.y_root - self._drag_data["y"]
        x = self.win.winfo_x() + dx
        y = self.win.winfo_y() + dy
        self.win.geometry(f"+{x}+{y}")
        self._drag_data["x"] = event.x_root
        self._drag_data["y"] = event.y_root

    def close(self):
        try:
            self.win.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    FocusApp()
