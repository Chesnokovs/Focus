"""
MainWindow — chrome of the Focus App (header, add-task bar, footer).

This iteration draws the layout per Design/Focus App/components/MainWindow.jsx
but does NOT yet render task cards (that's the next step). The task list area
shows an empty-state hint. Settings and shortcuts buttons are wired but only
toggle a placeholder state for now.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QSizePolicy, QScrollArea,
)

from app import fonts, icons, themes
from app.models import Store, Task
from app.widgets.task_card import TaskCard
from app.windows.focus_window import FocusWindow


def _h(*widgets, spacing: int = 0, margins=(0, 0, 0, 0)) -> QHBoxLayout:
    lay = QHBoxLayout()
    lay.setSpacing(spacing)
    lay.setContentsMargins(*margins)
    for w in widgets:
        if w is None:
            lay.addStretch(1)
        else:
            lay.addWidget(w)
    return lay


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
    """Square ghost-style button that holds a single icon."""
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
    """Tiny pulsing dot used in the footer and on running task cards."""
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
    def __init__(self, store: Store):
        super().__init__()
        self.store = store
        self.theme = themes.active_theme()

        # --- Pomodoro state ---
        self._pomodoro_remaining: int = self.store.settings.pomodoro_work
        self._is_break: bool = False
        self._tick_count: int = 0  # used for periodic save (every 30s)
        self._focus_window: FocusWindow | None = None
        self._focus_task_id: str | None = None  # task currently shown in overlay

        self._build_ui()

        # Tick every second; the handler is a no-op when no task is active.
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
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
        t = self.theme
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

        # Scrollable container for cards
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

        # Render initial cards (currently active task is None — wired in step 4)
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

        # Remove existing cards from the layout (keep empty hint + stretch markers).
        # Strategy: rebuild by inserting cards at the top, before empty hint.
        if not self.store.tasks:
            self._empty_hint.show()
            return
        self._empty_hint.hide()

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
        card.nameEdited.connect(self._on_name_edited)
        card.descriptionEdited.connect(self._on_description_edited)
        card.imageAddRequested.connect(self._on_images_added)
        card.imageRemoveRequested.connect(self._on_image_removed)
        return card

    # --- Task action handlers ---

    def _on_add_task(self) -> None:
        text = self.entry.text().strip()
        if not text:
            return
        task = Task(text=text)
        self.store.tasks.append(task)
        # Insert the new card at the bottom (above the trailing stretch).
        card = self._make_card(task)
        insert_at = self._cards_layout.count() - 1  # before the stretch
        if self._empty_hint.isVisible():
            self._empty_hint.hide()
            # The empty hint occupied index 0 — the stretch is now at index 1.
            insert_at = self._cards_layout.count() - 1
        self._cards_layout.insertWidget(insert_at, card)
        self._cards[task.id] = card
        self.entry.clear()
        self._active_label.setText(f"{self.store.active_count()} active")
        self.store.save()

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
        self.store.save()

    def _on_start(self, task_id: str) -> None:
        # Fresh start — reset Pomodoro to a full work phase.
        self._is_break = False
        self._pomodoro_remaining = self.store.settings.pomodoro_work
        self._set_active(task_id)
        self._refresh_status_label()
        self._open_focus_window(task_id, paused=False)

    def _on_resume(self, task_id: str) -> None:
        # Resume — keep the existing Pomodoro countdown.
        self._set_active(task_id)
        self._refresh_status_label()
        self._open_focus_window(task_id, paused=False)

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
        self._refresh_status_label()
        self._close_focus_window()
        self.store.save()

    def _on_pause(self, task_id: str) -> None:
        task = self.store.find(task_id)
        if task is None:
            return
        task.paused = True
        if self._active_task_id == task_id:
            self._active_task_id = None
        if task_id in self._cards:
            self._cards[task_id].update_state(task=task, is_active=False)
        self._refresh_status_label()
        # Keep the FocusWindow open and show paused state
        if self._focus_window is not None and self._focus_task_id == task_id:
            self._focus_window.set_paused(True)
        self.store.save()

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
        self._active_label.setText(f"{self.store.active_count()} active")
        self._refresh_status_label()
        if self._focus_task_id == task_id:
            self._close_focus_window()
        self.store.save()

    def _on_delete(self, task_id: str) -> None:
        if task_id in self._cards:
            card = self._cards.pop(task_id)
            card.setParent(None)
            card.deleteLater()
        self.store.tasks = [t for t in self.store.tasks if t.id != task_id]
        if self._expanded_task_id == task_id:
            self._expanded_task_id = None
        if self._active_task_id == task_id:
            self._active_task_id = None
        if not self.store.tasks:
            self._empty_hint.show()
        self._active_label.setText(f"{self.store.active_count()} active")
        self._refresh_status_label()
        if self._focus_task_id == task_id:
            self._close_focus_window()
        self.store.save()

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
        self._focus_task_id = task_id
        self._focus_window.set_task(task.text)
        self._focus_window.set_phase(self._is_break)
        self._focus_window.set_paused(paused)
        total = (self.store.settings.pomodoro_break if self._is_break
                 else self.store.settings.pomodoro_work)
        self._focus_window.set_remaining(self._pomodoro_remaining, total)
        self._focus_window.show()

    def _close_focus_window(self) -> None:
        if self._focus_window is not None:
            self._focus_window.hide()
        self._focus_task_id = None

    # --- 1Hz Pomodoro tick ---

    def _on_tick(self) -> None:
        aid = self._active_task_id
        if aid is None:
            return
        task = self.store.find(aid)
        if task is None:
            return

        # Track work-phase seconds against the task and today's stats.
        if not self._is_break:
            task.time_spent += 1
            self.store.stats.add_seconds(1)
            if aid in self._cards:
                self._cards[aid].set_displayed_time(task.time_spent)
            self._refresh_today_label()

        # Pomodoro countdown
        self._pomodoro_remaining -= 1
        if self._pomodoro_remaining <= 0:
            self._switch_phase()

        # Push state to the FocusWindow if open
        if self._focus_window is not None and self._focus_task_id == aid:
            total = (self.store.settings.pomodoro_break if self._is_break
                     else self.store.settings.pomodoro_work)
            self._focus_window.set_remaining(self._pomodoro_remaining, total)

        # Disk save every 30 ticks (~30s) — smooth out IO.
        self._tick_count = (self._tick_count + 1) % 30
        if self._tick_count == 0:
            self.store.save()

    def _switch_phase(self) -> None:
        if self._is_break:
            self._is_break = False
            self._pomodoro_remaining = self.store.settings.pomodoro_work
        else:
            self._is_break = True
            self._pomodoro_remaining = self.store.settings.pomodoro_break
        if self._focus_window is not None:
            self._focus_window.set_phase(self._is_break)

    # --- Save on close ---

    def closeEvent(self, event):
        self.store.save()
        if self._focus_window is not None:
            self._focus_window.close()
        super().closeEvent(event)

    def _on_name_edited(self, task_id: str, new_text: str) -> None:
        task = self.store.find(task_id)
        if task is None or task.text == new_text:
            return
        task.text = new_text
        # Refresh the card so the title in the header updates too.
        self._refresh_card_expansion(task_id)
        self.store.save()

    def _on_description_edited(self, task_id: str, new_text: str) -> None:
        task = self.store.find(task_id)
        if task is None:
            return
        task.description = new_text
        # No card refresh needed — only the indicator (paperclip) might change,
        # but it's already showing while expanded. Skipping refresh keeps focus
        # in the textarea.
        self.store.save()

    def _on_images_added(self, task_id: str, paths: list[str]) -> None:
        task = self.store.find(task_id)
        if task is None:
            return
        task.images.extend(paths)
        self._refresh_card_expansion(task_id)
        self.store.save()

    def _on_image_removed(self, task_id: str, index: int) -> None:
        task = self.store.find(task_id)
        if task is None or not (0 <= index < len(task.images)):
            return
        task.images.pop(index)
        self._refresh_card_expansion(task_id)
        self.store.save()

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

        self._status_lbl = QLabel("Idle")
        self._status_lbl.setFont(fonts.ui(11))
        self._status_lbl.setStyleSheet(f"color: {t.S_TEXT_MUTED};")
        lay.addWidget(self._status_lbl)

        lay.addStretch(1)

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

    # --- Footer live updates ---

    def _refresh_today_label(self) -> None:
        secs = self.store.stats.today_seconds()
        h, m = secs // 3600, (secs % 3600) // 60
        self._today_lbl.setText(f"Today · {h}h {m:02d}m")

    def _refresh_streak_label(self) -> None:
        self._streak_lbl.setText(f"Streak {self.store.stats.streak_days()}d")

    def _refresh_status_label(self) -> None:
        if self._active_task_id is None:
            self._running_dot.hide()
            self._status_lbl.setText("Idle")
            return
        task = self.store.find(self._active_task_id)
        if task is None:
            self._running_dot.hide()
            self._status_lbl.setText("Idle")
            return
        self._running_dot.show()
        self._status_lbl.setText(f"Focusing · {task.text}")
