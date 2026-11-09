"""
FocusWindow — frameless always-on-top focus overlay (V4 layout).

Composition (top → bottom, 14px padding):
  1. Eyebrow row: 7×7 pulsing dot + "FOCUSING ON" caption.
  2. Big task title (Inter 32pt Bold, max 2 lines, ellipsis).
  3. Bottom row: timer chip (mini ring + timer + WORK/BREAK suffix) — buttons (pause/done/stop).

State updates pushed from MainWindow's 1Hz timer.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QPoint, QRectF, QSize, Signal
from PySide6.QtGui import (
    QColor, QFont, QLinearGradient, QPainter, QPainterPath,
    QFontMetrics, QMouseEvent,
)
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)

from app import fonts, icons, themes
from app.widgets.circular_progress import CircularProgress
from app.widgets.pulsing_dot import PulsingDot


CARD_W, CARD_H = 440, 158
SHADOW_MARGIN = 22  # leaves room around the card for the drop shadow


class _Card(QFrame):
    """Visible 440×158 surface — rounded gradient + 1px inset highlight."""

    def __init__(self, bg_top: str, bg_bottom: str, *, radius: int = 16):
        super().__init__()
        self.setFixedSize(CARD_W, CARD_H)
        self._bg_top = QColor(bg_top)
        self._bg_bottom = QColor(bg_bottom)
        self._radius = radius
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def set_bg(self, top: str, bottom: str):
        self._bg_top = QColor(top)
        self._bg_bottom = QColor(bottom)
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(0, 0, self.width(), self.height())
        path = QPainterPath()
        path.addRoundedRect(rect, self._radius, self._radius)

        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, self._bg_top)
        grad.setColorAt(1.0, self._bg_bottom)
        p.fillPath(path, grad)

        # Inset highlight at top edge
        p.setClipPath(path)
        p.fillRect(QRectF(0, 0, self.width(), 1), QColor(255, 255, 255, 31))
        p.end()


class _ElidedTitle(QLabel):
    """QLabel that does multi-line elision (max 2 lines + ellipsis)."""

    def __init__(self, *, max_lines: int = 2):
        super().__init__()
        self._raw = ""
        self._max_lines = max_lines
        self.setWordWrap(False)  # we draw manually
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def setText(self, text: str) -> None:  # type: ignore[override]
        self._raw = text or ""
        super().setText("")  # we paint ourselves; keep label empty for sizing
        self.update()

    def text(self) -> str:  # type: ignore[override]
        return self._raw

    def sizeHint(self) -> QSize:
        fm = self.fontMetrics()
        return QSize(super().sizeHint().width(),
                     int(fm.lineSpacing() * self._max_lines))

    def paintEvent(self, _event):
        if not self._raw:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(self.palette().color(self.foregroundRole()))
        p.setFont(self.font())

        fm = QFontMetrics(self.font())
        line_h = fm.lineSpacing()
        words = self._raw.split()
        lines: list[str] = []
        current = ""
        i = 0
        max_w = self.width()
        while i < len(words) and len(lines) < self._max_lines:
            tentative = current + (" " if current else "") + words[i]
            if fm.horizontalAdvance(tentative) <= max_w:
                current = tentative
                i += 1
            elif not current:
                # Single word longer than line — chop it.
                current = words[i]
                i += 1
            else:
                lines.append(current)
                current = ""
        if current and len(lines) < self._max_lines:
            lines.append(current)

        # If text remains and we're at the last line, elide it.
        if i < len(words) and lines:
            remainder = lines[-1] + " " + " ".join(words[i:])
            lines[-1] = fm.elidedText(remainder, Qt.TextElideMode.ElideRight, max_w)

        y = fm.ascent()
        for line in lines:
            p.drawText(0, y, line)
            y += line_h
        p.end()


class _TimerChip(QWidget):
    """Dark pill containing: mini ring + timer + WORK/BREAK suffix."""

    def __init__(self, *, theme: themes.Theme):
        super().__init__()
        self._theme = theme
        self.setObjectName("timerChip")
        self.setStyleSheet("""
            QWidget#timerChip {
                background-color: rgba(0, 0, 0, 0.22);
                border-radius: 10px;
            }
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 8, 6)
        lay.setSpacing(10)

        self.ring = CircularProgress(
            size=24, stroke=2.0,
            track_color="rgba(255,255,255,0.20)",
            progress_color="#FFFFFF",
        )
        lay.addWidget(self.ring, 0, Qt.AlignmentFlag.AlignVCenter)

        self.timer_lbl = QLabel("25:00")
        self.timer_lbl.setFont(fonts.mono(22, QFont.Weight.Bold))
        self.timer_lbl.setStyleSheet("color: #FFFFFF; letter-spacing: -0.5px;")
        lay.addWidget(self.timer_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        self.suffix_lbl = QLabel("WORK")
        self.suffix_lbl.setFont(fonts.ui(10, QFont.Weight.DemiBold))
        self.suffix_lbl.setStyleSheet(
            "color: rgba(255,255,255,0.70); letter-spacing: 1.2px;"
        )
        lay.addWidget(self.suffix_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)


class FocusWindow(QWidget):
    pauseRequested  = Signal()
    resumeRequested = Signal()
    doneRequested   = Signal()
    stopRequested   = Signal()
    openRequested   = Signal()   # double-click: bring the main window back

    def __init__(self, *, theme: themes.Theme | None = None):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        self._theme = theme or themes.active_theme()
        self._is_paused = False
        self._is_break = False
        self._drag_offset: QPoint | None = None

        self.resize(CARD_W + 2 * SHADOW_MARGIN, CARD_H + 2 * SHADOW_MARGIN)
        self._position_top_right()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(SHADOW_MARGIN, SHADOW_MARGIN, SHADOW_MARGIN, SHADOW_MARGIN)
        outer.setSpacing(0)

        bg_top, bg_bottom = self._bg_colors()
        self._card = _Card(bg_top, bg_bottom, radius=16)
        outer.addWidget(self._card, alignment=Qt.AlignmentFlag.AlignCenter)

        eff = QGraphicsDropShadowEffect(self)
        eff.setBlurRadius(36)
        eff.setOffset(0, 14)
        eff.setColor(QColor(0, 0, 0, 150))
        self._card.setGraphicsEffect(eff)

        self._build_card_contents()

    # --- Public API ---

    def set_task(self, title: str) -> None:
        self._title.setText(title or "")
        self.setToolTip(f"{title or ''}\nDouble-click to open Focus".strip())

    def set_remaining(self, remaining_seconds: int, total_seconds: int) -> None:
        rem = max(0, int(remaining_seconds))
        total = max(1, int(total_seconds))
        elapsed = total - rem
        self._chip.ring.set_progress(max(0.0, min(1.0, elapsed / total)))
        self._chip.timer_lbl.setText(self._fmt_time(rem))

    def set_phase(self, is_break: bool) -> None:
        if is_break == self._is_break:
            self._refresh_suffix()
            return
        self._is_break = is_break
        if is_break:
            self._chip.timer_lbl.setStyleSheet(
                f"color: {self._theme.S_GREEN}; letter-spacing: -0.5px;"
            )
            self._chip.ring.set_progress_color(self._theme.S_GREEN)
        else:
            self._chip.timer_lbl.setStyleSheet(
                "color: #FFFFFF; letter-spacing: -0.5px;"
            )
            self._chip.ring.set_progress_color("#FFFFFF")
        self._refresh_suffix()

    def set_paused(self, is_paused: bool) -> None:
        if is_paused == self._is_paused:
            return
        self._is_paused = is_paused
        self._pause_btn.setIcon(icons.icon("play" if is_paused else "pause", white=True))
        self._pause_btn.setToolTip("Resume" if is_paused else "Pause")
        if is_paused:
            self._dot.stop()
        else:
            self._dot.start()
        self.setWindowOpacity(0.85 if is_paused else 1.0)
        self._refresh_eyebrow()

    # --- Internal ---

    def _bg_colors(self) -> tuple[str, str]:
        return ("#DC2626", "#B91C1C")

    def _fmt_time(self, seconds: int) -> str:
        seconds = max(0, int(seconds))
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def _refresh_suffix(self) -> None:
        self._chip.suffix_lbl.setText("BREAK" if self._is_break else "WORK")
        self._refresh_eyebrow()

    def _refresh_eyebrow(self) -> None:
        if self._is_paused:
            text = "PAUSED"
        elif self._is_break:
            text = "ON A BREAK"
        else:
            text = "FOCUSING ON"
        self._eyebrow_lbl.setText(text)

    def _position_top_right(self) -> None:
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        x = geo.right() - self.width() + 4   # account for shadow margin
        y = geo.top() + 4
        self.move(x, y)

    def _build_card_contents(self) -> None:
        layout = QVBoxLayout(self._card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(0)

        # 1. Eyebrow
        eyebrow = QHBoxLayout()
        eyebrow.setContentsMargins(0, 0, 0, 0)
        eyebrow.setSpacing(8)
        self._dot = PulsingDot(size=7, color="#FFFFFF", duration_ms=1600)
        eyebrow.addWidget(self._dot, 0, Qt.AlignmentFlag.AlignVCenter)
        eyebrow_lbl = QLabel("FOCUSING ON")
        eyebrow_lbl.setFont(fonts.ui(11, QFont.Weight.Bold))
        eyebrow_lbl.setStyleSheet(
            "color: rgba(255,255,255,0.90); letter-spacing: 1.4px;"
        )
        self._eyebrow_lbl = eyebrow_lbl
        eyebrow.addWidget(eyebrow_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        eyebrow.addStretch(1)
        eyebrow_w = QWidget()
        eyebrow_w.setLayout(eyebrow)
        layout.addWidget(eyebrow_w)

        layout.addSpacing(4)  # margin-top on title

        # 2. Title
        self._title = _ElidedTitle(max_lines=2)
        self._title.setFont(fonts.ui(28, QFont.Weight.Bold))
        self._title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(self._title)

        layout.addStretch(1)

        # 3. Bottom row
        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, 0)
        bottom.setSpacing(12)

        self._chip = _TimerChip(theme=self._theme)
        bottom.addWidget(self._chip, 0, Qt.AlignmentFlag.AlignVCenter)

        bottom.addStretch(1)

        self._pause_btn = self._make_btn("pause", "Pause")
        self._pause_btn.clicked.connect(self._on_pause_or_resume_clicked)
        bottom.addWidget(self._pause_btn)

        self._done_btn = self._make_btn("check", "Done")
        self._done_btn.clicked.connect(self.doneRequested.emit)
        bottom.addWidget(self._done_btn)

        self._stop_btn = self._make_btn("stop", "Stop")
        self._stop_btn.clicked.connect(self.stopRequested.emit)
        bottom.addWidget(self._stop_btn)

        bottom_w = QWidget()
        bottom_w.setLayout(bottom)
        layout.addWidget(bottom_w)

        self._refresh_suffix()

    def _make_btn(self, icon_name: str, tooltip: str) -> QPushButton:
        btn = QPushButton()
        btn.setIcon(icons.icon(icon_name, white=True))
        btn.setIconSize(QSize(12, 12))
        btn.setFixedSize(30, 30)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.16);
                border: 1px solid rgba(255, 255, 255, 0.20);
                border-radius: 7px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.24);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.32);
            }
        """)
        return btn

    def _on_pause_or_resume_clicked(self):
        if self._is_paused:
            self.resumeRequested.emit()
        else:
            self.pauseRequested.emit()

    # --- Drag the window ---

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_offset is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.openRequested.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)
