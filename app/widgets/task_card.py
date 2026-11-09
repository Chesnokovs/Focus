"""
TaskCard — single-task row in the MainWindow list.

Step 3a: 4 collapsed states (idle/running/paused/done) with action buttons.
Step 3b: expanded panel (name edit, description, image strip, Ctrl+V/drop hints).

State derivation:
    paused == True            -> "paused"  (yellow ring + bars)
    is_active == True         -> "running" (red pulse)
    done == True              -> "done"    (green check)
    otherwise                 -> "idle"    (hollow ring)

Layout matches Design/Focus App/components/MainWindow.jsx :: TaskRow.
"""
from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QPixmap, QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QWidget, QVBoxLayout,
    QLineEdit, QPushButton, QFileDialog,
)

from app import fonts, icons, themes
from app.models import Task
from app.widgets.state_indicator import StateIndicator
from app.widgets.action_button import ActionButton
from app.widgets.description_edit import DescriptionEdit, collect_image_paths
from app.windows.image_viewer import ImageViewer


def format_time(seconds: int) -> str:
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class TaskCard(QFrame):
    """Task card with optional expanded panel."""

    expandRequested = Signal(str)
    startRequested  = Signal(str)
    stopRequested   = Signal(str)
    pauseRequested  = Signal(str)
    resumeRequested = Signal(str)
    doneRequested   = Signal(str)
    deleteRequested = Signal(str)
    nameEdited      = Signal(str, str)        # task_id, new_text
    descriptionEdited = Signal(str, str)      # task_id, new_text
    imageAddRequested = Signal(str, list)     # task_id, paths
    imageRemoveRequested = Signal(str, int)   # task_id, index

    def __init__(self, task: Task, *, is_active: bool = False,
                 is_expanded: bool = False, theme: themes.Theme | None = None):
        super().__init__()
        self._task = task
        self._is_active = is_active
        self._is_expanded = is_expanded
        self._theme = theme or themes.active_theme()
        # Allow dropping image files anywhere on the card while expanded.
        self.setAcceptDrops(True)
        self._build()

    @property
    def task_id(self) -> str:
        return self._task.id

    def set_displayed_time(self, seconds: int) -> None:
        """Update only the time label (used by the running timer — no rebuild)."""
        self._task.time_spent = seconds
        if getattr(self, "_time_lbl", None) is not None:
            self._time_lbl.setText(format_time(seconds))

    def update_state(self, *, task: Optional[Task] = None,
                     is_active: Optional[bool] = None,
                     is_expanded: Optional[bool] = None) -> None:
        if task is not None:
            self._task = task
        if is_active is not None:
            self._is_active = is_active
        if is_expanded is not None:
            self._is_expanded = is_expanded
        old = self.layout()
        if old is not None:
            QWidget().setLayout(old)
        self._build_contents()
        self._apply_card_style()

    # --- Build ---

    def _build(self) -> None:
        self._build_contents()
        self._apply_card_style()

    def _state_name(self) -> str:
        if self._task.paused:
            return "paused"
        if self._is_active:
            return "running"
        if self._task.done:
            return "done"
        return "idle"

    def _apply_card_style(self) -> None:
        t = self._theme
        if self._is_active:
            bg = (
                f"qlineargradient(x1:0, y1:0, x2:0, y2:1, "
                f"stop:0 {t.S_ACTIVE}, stop:1 {t.S_SURFACE})"
            )
            border = "rgba(239, 68, 68, 0.35)"
        else:
            bg = t.S_SURFACE
            border = t.S_BORDER

        self.setObjectName("taskCard")
        self.setStyleSheet(f"""
            QFrame#taskCard {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 10px;
            }}
            QFrame#taskCard QLabel {{ background: transparent; }}
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _build_contents(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._build_header_row())
        if self._is_expanded:
            outer.addWidget(self._build_expanded_panel())

    # --- Header (always visible) ---

    def _build_header_row(self) -> QWidget:
        t = self._theme
        state = self._state_name()

        wrap = QWidget()
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        self._indicator = StateIndicator(state, theme=t)
        layout.addWidget(self._indicator, 0, Qt.AlignmentFlag.AlignVCenter)

        # Title + LIVE + paperclip — clickable region for expand/collapse
        title_wrap = QWidget()
        tw_lay = QHBoxLayout(title_wrap)
        tw_lay.setContentsMargins(0, 0, 0, 0)
        tw_lay.setSpacing(8)

        title = QLabel(self._task.text or "(untitled)")
        weight = QFont.Weight.DemiBold if state == "running" else QFont.Weight.Medium
        title.setFont(fonts.ui(13, weight))
        title_color = t.S_DIM if state == "done" else t.S_FG
        style = f"color: {title_color};"
        if state == "done":
            style += " text-decoration: line-through;"
        title.setStyleSheet(style)
        title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tw_lay.addWidget(title)

        if state == "running":
            badge = QLabel("LIVE")
            badge.setFont(fonts.ui(10, QFont.Weight.Bold))
            badge.setStyleSheet(f"""
                color: {t.S_ACCENT};
                background-color: rgba(239, 68, 68, 0.12);
                padding: 2px 6px;
                border-radius: 4px;
            """)
            tw_lay.addWidget(badge, 0, Qt.AlignmentFlag.AlignVCenter)

        if self._task.images or self._task.description.strip():
            clip = QLabel()
            clip.setPixmap(icons.pixmap("paperclip"))
            clip.setToolTip("Has notes or attachments")
            tw_lay.addWidget(clip, 0, Qt.AlignmentFlag.AlignVCenter)

        title_wrap.setCursor(Qt.CursorShape.PointingHandCursor)
        title_wrap.mousePressEvent = lambda _e, tid=self._task.id: \
            self.expandRequested.emit(tid)
        layout.addWidget(title_wrap, 1)

        # Time
        time_lbl = QLabel(format_time(self._task.time_spent))
        time_color = t.S_FG if state == "running" else t.S_DIM
        time_weight = QFont.Weight.DemiBold if state == "running" else QFont.Weight.Medium
        time_lbl.setFont(fonts.mono(12, time_weight))
        time_lbl.setStyleSheet(f"color: {time_color};")
        time_lbl.setMinimumWidth(60)
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._time_lbl = time_lbl  # kept so timer can update without rebuild
        layout.addWidget(time_lbl)

        layout.addWidget(self._build_action_strip(state))
        return wrap

    def _build_action_strip(self, state: str) -> QWidget:
        wrap = QWidget()
        h = QHBoxLayout(wrap)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(4)
        t = self._theme

        if state == "running":
            pause = ActionButton("warn", "pause", theme=t)
            pause.clicked.connect(lambda: self.pauseRequested.emit(self._task.id))
            h.addWidget(pause)
            stop = ActionButton("stop", "stop", "Stop", theme=t)
            stop.clicked.connect(lambda: self.stopRequested.emit(self._task.id))
            h.addWidget(stop)
        elif state == "paused":
            resume = ActionButton("primary", "play", "Resume", theme=t)
            resume.clicked.connect(lambda: self.resumeRequested.emit(self._task.id))
            h.addWidget(resume)
        elif state == "idle":
            start = ActionButton("primary", "play", "Start", theme=t)
            start.clicked.connect(lambda: self.startRequested.emit(self._task.id))
            h.addWidget(start)

        if state in ("running", "paused", "idle"):
            done = ActionButton("ghost", "check", theme=t)
            done.setToolTip("Mark done")
            done.clicked.connect(lambda: self.doneRequested.emit(self._task.id))
            h.addWidget(done)

        if state == "done":
            inner = QWidget()
            inner_lay = QHBoxLayout(inner)
            inner_lay.setContentsMargins(8, 0, 8, 0)
            inner_lay.setSpacing(4)
            check_icon = QLabel()
            check_icon.setPixmap(icons.pixmap("check"))
            done_lbl = QLabel("Done")
            done_lbl.setFont(fonts.ui(11, QFont.Weight.DemiBold))
            done_lbl.setStyleSheet(f"color: {t.S_GREEN};")
            inner_lay.addWidget(check_icon)
            inner_lay.addWidget(done_lbl)
            h.addWidget(inner)

            delete = ActionButton("ghost", "close", theme=t)
            delete.setToolTip("Delete")
            delete.clicked.connect(lambda: self.deleteRequested.emit(self._task.id))
            h.addWidget(delete)

        return wrap

    # --- Expanded panel ---

    def _build_expanded_panel(self) -> QWidget:
        t = self._theme
        wrap = QFrame()
        wrap.setObjectName("expandPanel")
        wrap.setStyleSheet(f"""
            QFrame#expandPanel {{
                border-top: 1px solid {t.S_BORDER};
                background: transparent;
            }}
        """)
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(38, 12, 14, 14)
        lay.setSpacing(10)

        # Name editor (borderless + underline on focus)
        name_row = QHBoxLayout()
        name_row.setContentsMargins(0, 0, 0, 0)
        name_row.setSpacing(8)

        name_label = QLabel("Name")
        name_label.setFont(fonts.ui(11))
        name_label.setStyleSheet(f"color: {t.S_DIM};")
        name_label.setFixedWidth(42)
        name_row.addWidget(name_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self._name_edit = QLineEdit(self._task.text)
        self._name_edit.setFont(fonts.ui(13, QFont.Weight.Medium))
        self._name_edit.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                border-bottom: 1px solid {t.S_BORDER};
                color: {t.S_FG};
                padding: 4px 0;
            }}
            QLineEdit:focus {{
                border-bottom: 1px solid {t.S_ACCENT};
            }}
        """)
        self._name_edit.editingFinished.connect(self._on_name_finished)
        name_row.addWidget(self._name_edit, 1)
        lay.addLayout(name_row)

        # Description (paste-aware)
        self._desc_edit = DescriptionEdit()
        self._desc_edit.setPlainText(self._task.description)
        self._desc_edit.setFont(fonts.ui(12))
        self._desc_edit.setPlaceholderText("Notes, links, anything…")
        self._desc_edit.setMinimumHeight(72)
        self._desc_edit.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {t.S_BG};
                color: {t.S_FG};
                border: 1px solid {t.S_BORDER};
                border-radius: 6px;
                padding: 8px 10px;
            }}
            QPlainTextEdit:focus {{
                border: 1px solid {t.S_ACCENT};
            }}
        """)
        # Persist text on focus out
        self._desc_edit.focusOutEvent = self._wrap_focus_out(
            self._desc_edit.focusOutEvent, self._on_description_changed
        )
        # Forward pasted/dropped images on the description through to the card's signal
        self._desc_edit.imagesAdded.connect(
            lambda paths: self.imageAddRequested.emit(self._task.id, list(paths))
        )
        lay.addWidget(self._desc_edit)

        # Hint row + Add image button + Total
        lay.addLayout(self._build_hint_row())

        # Thumbnails
        if self._task.images:
            lay.addLayout(self._build_thumb_row())
        return wrap

    def _build_hint_row(self) -> QHBoxLayout:
        t = self._theme
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        # Kbd: Ctrl + V
        ctrl_kbd = self._kbd("Ctrl")
        plus = QLabel("+")
        plus.setFont(fonts.ui(11))
        plus.setStyleSheet(f"color: {t.S_DIM};")
        v_kbd = self._kbd("V")
        paste_lbl = QLabel("paste")
        paste_lbl.setFont(fonts.ui(11))
        paste_lbl.setStyleSheet(f"color: {t.S_DIM};")
        row.addWidget(ctrl_kbd)
        row.addWidget(plus)
        row.addWidget(v_kbd)
        row.addWidget(paste_lbl)

        # upload icon + "drop files"
        sep = QLabel("·")
        sep.setStyleSheet(f"color: {t.S_DIM};")
        sep.setFont(fonts.ui(11))
        row.addWidget(sep)
        upload_icon = QLabel()
        upload_icon.setPixmap(icons.pixmap("upload"))
        row.addWidget(upload_icon)
        drop_lbl = QLabel("drop files")
        drop_lbl.setFont(fonts.ui(11))
        drop_lbl.setStyleSheet(f"color: {t.S_DIM};")
        row.addWidget(drop_lbl)

        # + Image button
        self._add_img_btn = QPushButton("+ Image")
        self._add_img_btn.setFont(fonts.ui(11, QFont.Weight.Medium))
        self._add_img_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_img_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {t.S_TEXT_MUTED};
                border: 1px solid {t.S_BORDER};
                border-radius: 6px;
                padding: 4px 10px;
            }}
            QPushButton:hover {{ background: {t.S_SURFACE}; color: {t.S_FG}; }}
        """)
        self._add_img_btn.clicked.connect(self._on_add_image_clicked)
        row.addWidget(self._add_img_btn)

        row.addStretch(1)

        # Total time on the right
        total_label = QLabel("Total")
        total_label.setFont(fonts.ui(11))
        total_label.setStyleSheet(f"color: {t.S_DIM};")
        row.addWidget(total_label)
        total_value = QLabel(format_time(self._task.time_spent))
        total_value.setFont(fonts.mono(11, QFont.Weight.DemiBold))
        total_value.setStyleSheet(f"color: {t.S_FG};")
        row.addWidget(total_value)
        return row

    def _kbd(self, text: str) -> QLabel:
        t = self._theme
        lbl = QLabel(text)
        lbl.setFont(fonts.mono(10, QFont.Weight.Medium))
        lbl.setStyleSheet(f"""
            color: {t.S_TEXT_MUTED};
            background: {t.S_BG};
            border: 1px solid {t.S_BORDER};
            border-radius: 3px;
            padding: 1px 5px;
        """)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    def _build_thumb_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        for i, path in enumerate(self._task.images):
            row.addWidget(self._thumbnail(path, i))
        row.addStretch(1)
        return row

    def _thumbnail(self, path: str, index: int) -> QFrame:
        t = self._theme
        cell = QFrame()
        cell.setFixedSize(96, 110)
        cell.setStyleSheet(f"""
            QFrame {{
                background: {t.S_BG};
                border: 1px solid {t.S_BORDER};
                border-radius: 6px;
            }}
            QFrame:hover {{
                border: 1px solid {t.S_ACCENT};
            }}
        """)
        cell.setCursor(Qt.CursorShape.PointingHandCursor)
        cell.mousePressEvent = lambda _e, p=path: self._open_image_viewer(p)
        lay = QVBoxLayout(cell)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(2)

        thumb_lbl = QLabel()
        thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_lbl.setFixedSize(86, 80)
        if os.path.exists(path):
            pm = QPixmap(path)
            if not pm.isNull():
                pm = pm.scaled(QSize(86, 80),
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
                thumb_lbl.setPixmap(pm)
            else:
                thumb_lbl.setText("[err]")
                thumb_lbl.setStyleSheet(f"color: {t.S_RED};")
        else:
            thumb_lbl.setText("[missing]")
            thumb_lbl.setStyleSheet(f"color: {t.S_DIM};")
        lay.addWidget(thumb_lbl)

        # Filename + remove button
        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, 0)
        bottom.setSpacing(2)
        fname = os.path.basename(path)
        if len(fname) > 12:
            fname = fname[:9] + "…"
        fname_lbl = QLabel(fname)
        fname_lbl.setFont(fonts.ui(8))
        fname_lbl.setStyleSheet(f"color: {t.S_DIM};")
        bottom.addWidget(fname_lbl, 1)

        rm_btn = QPushButton("×")
        rm_btn.setFont(fonts.ui(10, QFont.Weight.Bold))
        rm_btn.setFixedSize(16, 16)
        rm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rm_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {t.S_RED};
                border: none;
            }}
            QPushButton:hover {{ background: {t.S_SURFACE}; border-radius: 4px; }}
        """)
        rm_btn.clicked.connect(lambda _=False, idx=index:
                               self.imageRemoveRequested.emit(self._task.id, idx))
        bottom.addWidget(rm_btn)
        lay.addLayout(bottom)
        return cell

    # --- Editing handlers ---

    def _on_name_finished(self):
        new = self._name_edit.text().strip()
        if new and new != self._task.text:
            self.nameEdited.emit(self._task.id, new)

    def _on_description_changed(self):
        new = self._desc_edit.toPlainText()
        if new != self._task.description:
            self.descriptionEdited.emit(self._task.id, new)

    @staticmethod
    def _wrap_focus_out(orig, on_focus_out):
        def handler(event):
            on_focus_out()
            orig(event)
        return handler

    def _on_add_image_clicked(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;All Files (*.*)"
        )
        if paths:
            self.imageAddRequested.emit(self._task.id, list(paths))

    def _open_image_viewer(self, path: str) -> None:
        viewer = ImageViewer(path, parent=self)
        viewer.exec()

    # --- Drag-drop image files anywhere on the card while expanded ---

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._is_expanded and collect_image_paths(event.mimeData()):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if self._is_expanded and collect_image_paths(event.mimeData()):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if self._is_expanded:
            paths = collect_image_paths(event.mimeData())
            if paths:
                self.imageAddRequested.emit(self._task.id, paths)
                event.acceptProposedAction()
                return
        super().dropEvent(event)
