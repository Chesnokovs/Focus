"""
PulsingDot — tiny circle that fades 1↔.4 on a 1.6s loop.
Used in the FocusWindow eyebrow as the "live" indicator.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget


class PulsingDot(QWidget):
    def __init__(self, *, size: int = 7, color: str = "#FFFFFF",
                 duration_ms: int = 1600):
        super().__init__()
        self.setFixedSize(size, size)
        self._color = QColor(color)
        self._opacity = 1.0

        self._anim = QVariantAnimation(self)
        self._anim.setStartValue(1.0)
        self._anim.setKeyValueAt(0.5, 0.4)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(duration_ms)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anim.setLoopCount(-1)
        self._anim.valueChanged.connect(self._on_pulse)
        self._anim.start()

    def stop(self):
        self._anim.stop()
        self._opacity = 0.5
        self.update()

    def start(self):
        if self._anim.state() != QVariantAnimation.State.Running:
            self._anim.start()

    def set_color(self, color: str):
        new = QColor(color)
        if new == self._color:
            return
        self._color = new
        self.update()

    def _on_pulse(self, v):
        try:
            self._opacity = float(v)
        except (TypeError, ValueError):
            return
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self._color)
        c.setAlphaF(self._opacity)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c)
        p.drawEllipse(self.rect())
        p.end()
