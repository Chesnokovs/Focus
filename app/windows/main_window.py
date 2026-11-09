"""
MainWindow — task list, Pomodoro state and the system-tray icon.

Layout follows Design/Focus App/components/MainWindow.jsx: header, add-task
bar, scrollable task cards, footer.

The window owns all state changes: cards and the FocusWindow only emit
requests, the `_on_*` handlers here mutate the Store and refresh the views.

Minimising or closing the window hides it to the tray; the app keeps timing.
It exits only through the tray menu's Quit (or when no tray is available).
"""
from __future__ import annotations

import time

from PySide6.QtCore import QEvent, Qt, QSize, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QMenu, QMessageBox, QPushButton, QFrame, QSizePolicy,
    QScrollArea, QSystemTrayIcon,
)

from app import fonts, icons, themes
from app.models import Store, Task, import_image, remove_image_file
from app.widgets.elided_label import ElidedLabel
from app.widgets.task_card import TaskCard
from app.windows.focus_window import FocusWindow


class Pill(QFrame):
    """Small label/value chip used for Work/Break and the active-count badge."""
    def __init__(self, label: str, value: str, suffix: str = "", *, t: themes.Theme):
        super().__init__()
        self.setObjectName("pill")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(6)
        lbl = QLabel(label)
        lbl.setFont(fonts.ui(11))
        lbl.setStyleSheet(f"color: {t.S_DIM};")
        lay.addWidget(lbl)
        # value + suffix tightly grouped (2px) per designer's mockup
        vw = QWidget()
        vlay = QHBoxLayout(vw)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(2)
        val = QLabel(value)
        val.setFont(fonts.mono(12, QFont.Weight.DemiBold))
        val.setStyleSheet(f"color: {t.S_FG};")
        vlay.addWidget(val)
        if suffix:
            sfx = QLabel(suffix)
            sfx.setFont(fonts.ui(10))
            sfx.setStyleSheet(f"color: {t.S_DIM};")
            vlay.addWidget(sfx)
        lay.addWidget(vw)


class IconButton(QPushButton):
    """Square ghost-style button that holds a single icon.

    Not used yet — kept for the settings button (see README, extension points).
    """
    def __init__(self, icon_name: str, tooltip: str = "", *, t: themes.Theme):
        super().__init__()
        self.setIcon(icons.icon(icon_name))
        self.setIconSize(QSize(14, 14))
        self.setFixedSize(30, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            self.setToolTip(tooltip)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {t.S_BORDER};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {t.S_SURFACE};
            }}
            QPushButton:pressed {{
                background-color: {t.S_ACTIVE};
            }}
        """)


class RunningDot(QFrame):
    """Tiny accent dot shown in the footer while a task is running."""
    def __init__(self, *, t: themes.Theme, size: int = 8):
        super().__init__()
        self.setFixedSize(size, size)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {t.S_ACCENT};
                border-radius: {size // 2}px;
            }}
        """)


class MainWindow(QMainWindow):
    TICK_MS = 250          # how often the clock is checked (not the count unit)
    SAVE_EVERY_S = 30      # tracked seconds between periodic saves
    MAX_CATCHUP_S = 60     # a longer gap means the PC slept — don't count it

    def __init__(self, store: Store):
        super().__init__()
        self.store = store
        self.theme = themes.active_theme()

        # --- Pomodoro state ---
        self._pomodoro_remaining: int = self.store.settings.pomodoro_work
        self._is_break: bool = False
        self._last_tick: float = time.monotonic()
        self._unsaved_seconds: int = 0
        self._focus_window: FocusWindow | None = None
        self._focus_task_id: str | None = None  # task currently shown in overlay

        # --- App lifecycle ---
        self._tray: QSystemTrayIcon | None = None
        self._tray_pause_action = None
        self._quitting: bool = False
        self._save_failed: bool = False

        self._build_ui()
        self._build_tray()
        self._refresh_status_label()

        # Time is measured against the monotonic clock, so a late or skipped
        # timer event never loses a second; the handler is a no-op when idle.
        self._timer = QTimer(self)
        self._timer.setInterval(self.TICK_MS)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    def _build_ui(self) -> None:
        t = self.theme
        self.setWindowTitle("Focus")
        self.resize(720, 650)
        self.setMinimumSize(600, 400)
        self.setStyleSheet(f"""
            QMainWindow, QWidget#root {{ background-color: {t.S_BG}; }}
            QFrame#pill {{
                background-color: {t.S_SURFACE};
                border: 1px solid {t.S_BORDER};
                border-radius: 6px;
            }}
            QFrame#headerBox {{
                background-color: {t.S_SURFACE};
                border: 1px solid {t.S_BORDER};
                border-radius: 6px;
            }}
            QFrame#addBar {{
                background-color: {t.S_SURFACE};
                border: 1px solid {t.S_BORDER};
                border-radius: 8px;
            }}
            QFrame#hSep {{
                background-color: {t.S_BORDER};
                max-height: 1px; min-height: 1px;
            }}
            QFrame#vSep {{
                background-color: {t.S_BORDER};
                max-width: 1px; min-width: 1px;
            }}
            QFrame#footer {{
                background-color: {t.S_BG_DEEP};
                border-top: 1px solid {t.S_BORDER};
            }}
            QLineEdit#newTask {{
                background: transparent;
                border: none;
                color: {t.S_FG};
                padding: 0;
            }}
            QLineEdit#newTask:focus {{ outline: none; }}
            QPushButton#addBtn {{
                background-color: {t.S_ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 700;
                letter-spacing: 0.4px;
                padding: 0 14px;
            }}
            QPushButton#addBtn:hover {{ background-color: {t.S_ACCENT_HOVER}; }}
            QLabel#emptyHint {{ color: {t.S_DIM}; }}
        """)

        root = QWidget(); root.setObjectName("root")
        root_lay = QVBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        root_lay.addWidget(self._build_header())
        root_lay.addWidget(self._sep_h())
        root_lay.addWidget(self._build_add_bar())
        root_lay.addWidget(self._build_task_list_area(), stretch=1)
        root_lay.addWidget(self._build_footer())

        self.setCentralWidget(root)

    def _sep_h(self) -> QFrame:
        sep = QFrame(); sep.setObjectName("hSep"); return sep

    def _sep_v(self) -> QFrame:
        sep = QFrame(); sep.setObjectName("vSep"); sep.setFixedHeight(14); return sep

    def _build_header(self) -> QWidget:
        t = self.theme
        wrap = QWidget()
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(22, 18, 22, 14)
        lay.setSpacing(14)

        # "Focus" title
        title = QLabel("Focus")
        title.setFont(fonts.ui(18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {t.S_FG};")
        lay.addWidget(title)

        # "{N} active" pill
        active_pill = QFrame()
        active_pill.setObjectName("pill")
        ap_lay = QHBoxLayout(active_pill)
        ap_lay.setContentsMargins(8, 2, 8, 2)
        ap_lay.setSpacing(0)
        self._active_label = QLabel(f"{self.store.active_count()} active")
        self._active_label.setFont(fonts.ui(11))
        self._active_label.setStyleSheet(f"color: {t.S_TEXT_MUTED};")
        ap_lay.addWidget(self._active_label)
        lay.addWidget(active_pill)

        lay.addStretch(1)

        # Pomodoro group: [Work 25m | Break 5m]
        pomo = QFrame()
        pomo.setObjectName("headerBox")
        pomo_lay = QHBoxLayout(pomo)
        pomo_lay.setContentsMargins(3, 3, 3, 3)
        pomo_lay.setSpacing(4)
        pomo_lay.addWidget(Pill("Work",  str(self.store.settings.pomodoro_work // 60),  "m", t=t))
        pomo_lay.addWidget(self._sep_v())
        pomo_lay.addWidget(Pill("Break", str(self.store.settings.pomodoro_break // 60), "m", t=t))
        lay.addWidget(pomo)

        return wrap

    def _build_add_bar(self) -> QWidget:
        wrap = QWidget()
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(22, 14, 22, 8)
        lay.setSpacing(10)

        bar = QFrame(); bar.setObjectName("addBar")
        bar.setFixedHeight(42)
        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(14, 0, 4, 0)
        bar_lay.setSpacing(8)

        plus_lbl = QLabel()
        plus_lbl.setPixmap(icons.pixmap("plus"))
        bar_lay.addWidget(plus_lbl)

        self.entry = QLineEdit()
        self.entry.setObjectName("newTask")
        self.entry.setPlaceholderText("Add a task and press Enter…")
        self.entry.setFont(fonts.ui(13))
        self.entry.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        bar_lay.addWidget(self.entry)

        self.btn_add = QPushButton("+ ADD TASK")
        self.btn_add.setObjectName("addBtn")
        self.btn_add.setFont(fonts.ui(11, QFont.Weight.Bold))
        self.btn_add.setFixedHeight(32)
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        bar_lay.addWidget(self.btn_add)

        # Wire Add Task: button click and Enter in the input both add a task.
        self.btn_add.clicked.connect(self._on_add_task)
        self.entry.returnPressed.connect(self._on_add_task)

        lay.addWidget(bar)
        return wrap

    def _build_task_list_area(self) -> QWidget:
        t = self.theme

        # Scrollable container for cards. Layout order is always:
        # [card, card, ..., empty hint, stretch].
        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(6)

        # Empty hint, shown when no tasks
        self._empty_hint = QLabel("No tasks yet. Add one above.")
        self._empty_hint.setObjectName("emptyHint")
        self._empty_hint.setFont(fonts.ui(13))
        self._empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cards_layout.addWidget(self._empty_hint)
        self._cards_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._cards_container)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        # Cards always fit the viewport width; nothing should scroll sideways.
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollArea > QWidget > QWidget {{ background: transparent; }}
            QScrollBar:vertical {{
                background: transparent; width: 8px; margin: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {t.S_BORDER}; border-radius: 4px; min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {t.S_DIM}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0; background: none;
            }}
        """)

        wrap = QWidget()
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(22, 4, 22, 14)
        lay.setSpacing(0)
        lay.addWidget(scroll)

        self._cards: dict[str, TaskCard] = {}
        self._active_task_id: str | None = None
        self._expanded_task_id: str | None = None
        self._refresh_all_cards()
        return wrap

    def _refresh_all_cards(self) -> None:
        """Wipe and rebuild the card list. Used on first paint and rare full
        refreshes; per-task changes should call _refresh_card(task_id) instead."""
        for c in self._cards.values():
            c.setParent(None)
            c.deleteLater()
        self._cards.clear()

        self._empty_hint.setVisible(not self.store.tasks)
        for i, task in enumerate(self.store.tasks):
            card = self._make_card(task)
            self._cards_layout.insertWidget(i, card)
            self._cards[task.id] = card

    def _make_card(self, task: Task) -> TaskCard:
        is_active = task.id == self._active_task_id
        is_expanded = task.id == self._expanded_task_id
        card = TaskCard(task, is_active=is_active, is_expanded=is_expanded, theme=self.theme)
        card.expandRequested.connect(self._on_expand_request)
        card.startRequested.connect(self._on_start)
        card.stopRequested.connect(self._on_stop)
        card.pauseRequested.connect(self._on_pause)
        card.resumeRequested.connect(self._on_resume)
        card.doneRequested.connect(self._on_done)
        card.deleteRequested.connect(self._on_delete)
        card.reopenRequested.connect(self._on_reopen)
        card.nameEdited.connect(self._on_name_edited)
        card.descriptionEdited.connect(self._on_description_edited)
        card.imageAddRequested.connect(self._on_images_added)
        card.imageRemoveRequested.connect(self._on_image_removed)
        return card

    # --- Persistence ---

    def _save(self) -> None:
        """Save the store and surface a failure in the footer."""
        ok = self.store.save()
        self._unsaved_seconds = 0
        if self._save_failed == ok:  # state flipped
            self._save_failed = not ok
            self._refresh_status_label()

    def flush(self) -> None:
        """Commit text still being typed in the expanded card, then save."""
        card = self._cards.get(self._expanded_task_id) if self._expanded_task_id else None
        if card is not None:
            card.commit_edits()
        self._save()

    def _after_state_change(self) -> None:
        """Common tail of every task-state handler."""
        self._active_label.setText(f"{self.store.active_count()} active")
        self._refresh_status_label()
        self._save()

    # --- Task action handlers ---

    def _on_add_task(self) -> None:
        text = self.entry.text().strip()
        if not text:
            return
        task = Task(text=text)
        self.store.tasks.append(task)
        card = self._make_card(task)
        # New cards go after the existing ones, right before the empty hint.
        self._cards_layout.insertWidget(self._cards_layout.indexOf(self._empty_hint), card)
        self._empty_hint.hide()
        self._cards[task.id] = card
        self.entry.clear()
        self._after_state_change()

    def _refresh_card_expansion(self, task_id: str) -> None:
        """Re-render a card with current expanded/active state."""
        if task_id not in self._cards:
            return
        task = self.store.find(task_id)
        if task is None:
            return
        self._cards[task_id].update_state(
            task=task,
            is_active=(task_id == self._active_task_id),
            is_expanded=(task_id == self._expanded_task_id),
        )

    def _on_expand_request(self, task_id: str) -> None:
        """Toggle expand for the clicked task. Only one card expanded at a time."""
        prev = self._expanded_task_id
        if prev == task_id:
            self._expanded_task_id = None
        else:
            self._expanded_task_id = task_id
        # Refresh affected cards only — fast and flicker-free in Qt.
        if prev and prev != task_id:
            self._refresh_card_expansion(prev)
        self._refresh_card_expansion(task_id)

    def _set_active(self, new_id: str | None) -> None:
        """Switch which task is the running one. Refreshes only the affected cards."""
        prev_id = self._active_task_id
        self._active_task_id = new_id
        self._last_tick = time.monotonic()  # the new task starts counting from now

        if new_id is not None:
            task = self.store.find(new_id)
            if task is not None:
                task.paused = False  # only clear paused on the task being activated
                if new_id in self._cards:
                    self._cards[new_id].update_state(task=task, is_active=True)

        if prev_id and prev_id != new_id:
            prev_task = self.store.find(prev_id)
            if prev_task is not None and prev_id in self._cards:
                self._cards[prev_id].update_state(task=prev_task, is_active=False)

    def _on_start(self, task_id: str) -> None:
        # Fresh start — reset Pomodoro to a full work phase.
        self._is_break = False
        self._pomodoro_remaining = self.store.settings.pomodoro_work
        self._set_active(task_id)
        self._open_focus_window(task_id, paused=False)
        self._after_state_change()

    def _on_resume(self, task_id: str) -> None:
        # Resume — keep the existing Pomodoro countdown.
        self._set_active(task_id)
        self._open_focus_window(task_id, paused=False)
        self._after_state_change()

    def _on_stop(self, task_id: str) -> None:
        # Stops without keeping it paused — the task returns to idle.
        task = self.store.find(task_id)
        if task is None:
            return
        task.paused = False
        if self._active_task_id == task_id:
            self._active_task_id = None
        if task_id in self._cards:
            self._cards[task_id].update_state(task=task, is_active=False)
        # Reset Pomodoro on full stop, so next Start begins fresh
        self._is_break = False
        self._pomodoro_remaining = self.store.settings.pomodoro_work
        if self._focus_task_id == task_id:
            self._close_focus_window()
        self._after_state_change()

    def _on_pause(self, task_id: str) -> None:
        task = self.store.find(task_id)
        if task is None:
            return
        task.paused = True
        if self._active_task_id == task_id:
            self._active_task_id = None
        if task_id in self._cards:
            self._cards[task_id].update_state(task=task, is_active=False)
        # Keep the FocusWindow open and show paused state
        if self._focus_window is not None and self._focus_task_id == task_id:
            self._focus_window.set_paused(True)
        self._after_state_change()

    def _on_done(self, task_id: str) -> None:
        task = self.store.find(task_id)
        if task is None:
            return
        task.done = True
        task.paused = False
        if self._active_task_id == task_id:
            self._active_task_id = None
        if task_id in self._cards:
            self._cards[task_id].update_state(task=task, is_active=False)
        if self._focus_task_id == task_id:
            self._close_focus_window()
        self._after_state_change()

    def _on_reopen(self, task_id: str) -> None:
        task = self.store.find(task_id)
        if task is None:
            return
        task.done = False
        self._refresh_card_expansion(task_id)
        self._after_state_change()

    def _confirm_delete(self, task: Task) -> bool:
        name = task.text if len(task.text) <= 60 else task.text[:57] + "…"
        answer = QMessageBox.question(
            self, "Delete task",
            f"Delete “{name}”?\n\nIts notes, images and tracked time will be removed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _on_delete(self, task_id: str) -> None:
        task = self.store.find(task_id)
        if task is None or not self._confirm_delete(task):
            return
        if task_id in self._cards:
            card = self._cards.pop(task_id)
            card.setParent(None)
            card.deleteLater()
        self.store.tasks = [t for t in self.store.tasks if t.id != task_id]
        for path in task.images:
            remove_image_file(path)
        if self._expanded_task_id == task_id:
            self._expanded_task_id = None
        if self._active_task_id == task_id:
            self._active_task_id = None
        if not self.store.tasks:
            self._empty_hint.show()
        if self._focus_task_id == task_id:
            self._close_focus_window()
        self._after_state_change()

    # --- FocusWindow lifecycle ---

    def _open_focus_window(self, task_id: str, *, paused: bool) -> None:
        task = self.store.find(task_id)
        if task is None:
            return
        if self._focus_window is None:
            self._focus_window = FocusWindow(theme=self.theme)
            self._focus_window.pauseRequested.connect(
                lambda: self._on_pause(self._focus_task_id) if self._focus_task_id else None
            )
            self._focus_window.resumeRequested.connect(
                lambda: self._on_resume(self._focus_task_id) if self._focus_task_id else None
            )
            self._focus_window.doneRequested.connect(
                lambda: self._on_done(self._focus_task_id) if self._focus_task_id else None
            )
            self._focus_window.stopRequested.connect(
                lambda: self._on_stop(self._focus_task_id) if self._focus_task_id else None
            )
            self._focus_window.openRequested.connect(self.show_from_tray)
        self._focus_task_id = task_id
        self._focus_window.set_task(task.text)
        self._focus_window.set_phase(self._is_break)
        self._focus_window.set_paused(paused)
        self._push_remaining()
        self._focus_window.show()

    def _close_focus_window(self) -> None:
        if self._focus_window is not None:
            self._focus_window.hide()
        self._focus_task_id = None

    def _push_remaining(self) -> None:
        if self._focus_window is None:
            return
        total = (self.store.settings.pomodoro_break if self._is_break
                 else self.store.settings.pomodoro_work)
        self._focus_window.set_remaining(self._pomodoro_remaining, total)

    # --- Pomodoro clock ---

    def _on_tick(self) -> None:
        now = time.monotonic()
        aid = self._active_task_id
        task = self.store.find(aid) if aid else None
        if task is None:
            self._last_tick = now
            return

        whole = int(now - self._last_tick)
        if whole < 1:
            return
        self._last_tick += whole
        if whole > self.MAX_CATCHUP_S:
            whole = 1  # the machine slept or the app was frozen — not focus time

        for _ in range(whole):
            self._advance_second(task)

        if aid in self._cards:
            self._cards[aid].set_displayed_time(task.time_spent)
        self._refresh_today_label()
        if self._focus_task_id == aid:
            self._push_remaining()

        # Periodic save, so a crash loses at most SAVE_EVERY_S seconds.
        if self._unsaved_seconds >= self.SAVE_EVERY_S:
            self._save()

    def _advance_second(self, task: Task) -> None:
        # Only work-phase seconds count against the task and today's stats.
        if not self._is_break:
            task.time_spent += 1
            self.store.stats.add_seconds(1)
            if self.store.stats.today_seconds() == 1:
                # First focused second of the day extends the streak.
                self._refresh_streak_label()
        self._unsaved_seconds += 1

        self._pomodoro_remaining -= 1
        if self._pomodoro_remaining <= 0:
            self._switch_phase(task)

    def _switch_phase(self, task: Task) -> None:
        if self._is_break:
            self._is_break = False
            self._pomodoro_remaining = self.store.settings.pomodoro_work
            self._notify("Back to work", task.text)
        else:
            self._is_break = True
            self._pomodoro_remaining = self.store.settings.pomodoro_break
            minutes = self.store.settings.pomodoro_break // 60
            self._notify("Time for a break", f"{minutes} min · {task.text}")
        if self._focus_window is not None:
            self._focus_window.set_phase(self._is_break)
        self._refresh_status_label()

    def _notify(self, title: str, message: str) -> None:
        """Announce a phase change — the overlay's colour alone is easy to miss."""
        QApplication.beep()
        if self._tray is not None and self._tray.supportsMessages():
            self._tray.showMessage(
                title, message, QSystemTrayIcon.MessageIcon.Information, 5000
            )

    # --- System tray & window lifecycle ---

    def _build_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        icon = QApplication.windowIcon()
        if icon.isNull():
            # An icon-less tray entry is invisible: a hidden window could
            # never be brought back. Fall back to plain window behaviour.
            return
        tray = QSystemTrayIcon(icon, self)
        menu = QMenu(self)
        menu.addAction("Open Focus").triggered.connect(lambda *_: self.show_from_tray())
        self._tray_pause_action = menu.addAction("Pause")
        self._tray_pause_action.triggered.connect(lambda *_: self._on_tray_pause_resume())
        menu.addSeparator()
        menu.addAction("Quit").triggered.connect(lambda *_: self.quit_app())
        tray.setContextMenu(menu)
        tray.activated.connect(self._on_tray_activated)
        tray.show()
        self._tray = tray

    @property
    def has_tray(self) -> bool:
        return self._tray is not None

    def _on_tray_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger,
                      QSystemTrayIcon.ActivationReason.DoubleClick):
            self.show_from_tray()

    def _on_tray_pause_resume(self) -> None:
        if self._active_task_id is not None:
            self._on_pause(self._active_task_id)
        elif self._focus_task_id is not None:
            self._on_resume(self._focus_task_id)

    def _refresh_tray(self) -> None:
        if self._tray is None:
            return
        running = self._active_task_id is not None
        paused = not running and self._focus_task_id is not None
        self._tray_pause_action.setText("Resume" if paused else "Pause")
        self._tray_pause_action.setEnabled(running or paused)

        shown_id = self._active_task_id or self._focus_task_id
        task = self.store.find(shown_id) if shown_id else None
        if task is None:
            tip = "Focus — idle"
        else:
            # Windows cuts tray tooltips at 127 characters.
            name = task.text if len(task.text) <= 80 else task.text[:79] + "…"
            tip = f"Focus — {'paused' if paused else 'focusing'}: {name}"
        self._tray.setToolTip(tip)

    def show_from_tray(self) -> None:
        """Bring the main window back (tray click, overlay double-click, 2nd launch)."""
        self.setWindowState(
            (self.windowState() & ~Qt.WindowState.WindowMinimized)
            | Qt.WindowState.WindowActive
        )
        self.show()
        self.raise_()
        self.activateWindow()

    def _hide_to_tray(self) -> None:
        self.hide()
        if (self._tray is not None and not self.store.settings.tray_hint_shown
                and self._tray.supportsMessages()):
            self._tray.showMessage(
                "Focus is still running",
                "It lives in the system tray now. Right-click the icon to quit.",
                QSystemTrayIcon.MessageIcon.Information, 6000,
            )
            self.store.settings.tray_hint_shown = True
            self._save()

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if (event.type() == QEvent.Type.WindowStateChange
                and self.isMinimized() and self._tray is not None):
            # Hiding from inside the state-change event confuses Windows;
            # do it once the event has been fully delivered.
            QTimer.singleShot(0, self._hide_if_minimized)

    def _hide_if_minimized(self) -> None:
        if self.isMinimized():
            self._hide_to_tray()

    def closeEvent(self, event) -> None:
        if self._tray is not None and not self._quitting:
            # Closing only hides the window; Quit is in the tray menu.
            event.ignore()
            self._hide_to_tray()
            return
        super().closeEvent(event)
        if not self._quitting:
            self.quit_app()

    def prepare_for_session_end(self) -> None:
        """Windows is logging off or shutting down: save and stop refusing to close."""
        self._quitting = True
        self.flush()

    def quit_app(self) -> None:
        self._quitting = True
        self.flush()
        if self._focus_window is not None:
            self._focus_window.close()
        if self._tray is not None:
            self._tray.hide()
        QApplication.quit()

    # --- Card edit handlers ---

    def _on_name_edited(self, task_id: str, new_text: str) -> None:
        task = self.store.find(task_id)
        if task is None or task.text == new_text:
            return
        task.text = new_text
        # Refresh the card so the title in the header updates too.
        self._refresh_card_expansion(task_id)
        if self._focus_window is not None and self._focus_task_id == task_id:
            self._focus_window.set_task(new_text)
        self._after_state_change()

    def _on_description_edited(self, task_id: str, new_text: str) -> None:
        task = self.store.find(task_id)
        if task is None:
            return
        task.description = new_text
        # No card refresh needed — only the indicator (paperclip) might change,
        # but it's already showing while expanded. Skipping refresh keeps focus
        # in the textarea.
        self._save()

    def _on_images_added(self, task_id: str, paths: list[str]) -> None:
        task = self.store.find(task_id)
        if task is None:
            return
        # Copy into our images folder so the attachment survives the original
        # being moved or deleted.
        imported = [p for p in (import_image(src) for src in paths) if p]
        if not imported:
            return
        task.images.extend(imported)
        self._refresh_card_expansion(task_id)
        self._save()

    def _on_image_removed(self, task_id: str, index: int) -> None:
        task = self.store.find(task_id)
        if task is None or not (0 <= index < len(task.images)):
            return
        remove_image_file(task.images.pop(index))
        self._refresh_card_expansion(task_id)
        self._save()

    # --- Footer ---

    def _build_footer(self) -> QWidget:
        t = self.theme
        footer = QFrame()
        footer.setObjectName("footer")
        footer.setFixedHeight(28)
        lay = QHBoxLayout(footer)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(14)

        # Running indicator + status label (kept for live updates)
        self._running_dot = RunningDot(t=t)
        self._running_dot.hide()
        lay.addWidget(self._running_dot)

        # Takes the free width and elides, so a long task name can't push
        # Today / Streak out of the window.
        self._status_lbl = ElidedLabel("Idle", font=fonts.ui(11), color=t.S_TEXT_MUTED)
        lay.addWidget(self._status_lbl, 1)

        self._today_lbl = QLabel()
        self._today_lbl.setFont(fonts.mono(11))
        self._today_lbl.setStyleSheet(f"color: {t.S_TEXT_MUTED};")
        lay.addWidget(self._today_lbl)
        self._refresh_today_label()

        lay.addWidget(self._sep_v())

        self._streak_lbl = QLabel()
        self._streak_lbl.setFont(fonts.ui(11))
        self._streak_lbl.setStyleSheet(f"color: {t.S_TEXT_MUTED};")
        lay.addWidget(self._streak_lbl)
        self._refresh_streak_label()

        return footer

    def _refresh_today_label(self) -> None:
        secs = self.store.stats.today_seconds()
        h, m = secs // 3600, (secs % 3600) // 60
        self._today_lbl.setText(f"Today · {h}h {m:02d}m")

    def _refresh_streak_label(self) -> None:
        self._streak_lbl.setText(f"Streak {self.store.stats.streak_days()}d")

    def _refresh_status_label(self) -> None:
        t = self.theme
        task = self.store.find(self._active_task_id) if self._active_task_id else None
        if self._save_failed:
            self._running_dot.hide()
            self._status_lbl.set_color(t.S_RED)
            self._status_lbl.setText("Changes are not being saved — see focus.log")
        else:
            self._running_dot.setVisible(task is not None)
            self._status_lbl.set_color(t.S_TEXT_MUTED)
            if task is None:
                self._status_lbl.setText("Idle")
            else:
                phase = "Break" if self._is_break else "Focusing"
                self._status_lbl.setText(f"{phase} · {task.text}")
        self._refresh_tray()
