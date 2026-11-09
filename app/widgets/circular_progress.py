"""
CircularProgress — small ring rendered with QPainter. Used inside FocusWindow.

Track ring (background) and progress arc (foreground) are drawn separately.
Progress runs counter-clockwise from 12 o'clock (matches designer's mockup).
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class CircularProgress(QWidget):
    def __init__(self, *, size: int = 38, stroke: float = 2.5,
                 track_color: str = "rgba(255,255,255,0.20)",
                 progress_color: str = "#FFFFFF"):
        super().__init__()
        self.setFixedSize(size, size)
        self._stroke = stroke
        self._track = QColor.fromString(track_color) if hasattr(QColor, "fromString") else QColor(track_color)
        # Fallback for older PySide6 — parse rgba manually if needed.
        if not self._track.isValid():
            self._track = QColor(255, 255, 255, 51)  # ~20% white
        self._progress_color = QColor(progress_color)
        self._progress = 0.0  # 0..1

    def set_progress(self, value: float) -> None:
        v = max(0.0, min(1.0, float(value)))
        if v == self._progress:
            return
        self._progress = v
        self.update()

    def set_progress_color(self, color: str) -> None:
        new = QColor(color)
        if new == self._progress_color:
            return
        self._progress_color = new
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self._stroke
        rect = QRectF(s, s, self.width() - 2 * s, self.height() - 2 * s)

        # Track
        track_pen = QPen(self._track)
        track_pen.setWidthF(s)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(track_pen)
        p.drawEllipse(rect)

        # Progress arc — Qt arc angles are in 1/16 degree, 0° at 3 o'clock,
        # positive counter-clockwise. Start at 12 (=90°), sweep clockwise (negative).
        if self._progress > 0:
            prog_pen = QPen(self._progress_color)
            prog_pen.setWidthF(s)
            prog_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(prog_pen)
            start_angle = 90 * 16
            span_angle = -int(self._progress * 360 * 16)
            p.drawArc(rect, start_angle, span_angle)
        p.end()
