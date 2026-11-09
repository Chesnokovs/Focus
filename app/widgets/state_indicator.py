"""
StateIndicator — small 16x16 dot that visually conveys task state:

    idle    : hollow grey ring (1.5 px stroke, 70% opacity)
    running : solid red dot inside a red ring; the inner dot pulses
    paused  : yellow ring with two yellow vertical bars inside
    done    : solid green disc with a white check mark

The pulse is driven by QVariantAnimation (no QGraphicsOpacityEffect — that
adds offscreen compositing overhead for a tiny widget).
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QPen, QColor, QBrush
from PySide6.QtWidgets import QWidget

from app import themes

State = str  # 'idle' | 'running' | 'paused' | 'done'


class StateIndicator(QWidget):
    SIZE = 16

    def __init__(self, state: State = "idle", *, theme: themes.Theme | None = None):
        super().__init__()
        self.setFixedSize(self.SIZE, self.SIZE)
        self._theme = theme or themes.active_theme()
        self._state: State = state
        self._pulse: float = 1.0
        self._anim = QVariantAnimation(self)
        self._anim.setStartValue(1.0)
        self._anim.setKeyValueAt(0.5, 0.4)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(1400)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anim.setLoopCount(-1)
        self._anim.valueChanged.connect(self._on_pulse)
        if state == "running":
            self._anim.start()

    def set_state(self, state: State) -> None:
        if state == self._state:
            return
        self._state = state
        if state == "running":
            self._anim.start()
        else:
            self._anim.stop()
            self._pulse = 1.0
        self.update()

    def _on_pulse(self, value):
        try:
            self._pulse = float(value)
        except (TypeError, ValueError):
            return
        self.update()

    def paintEvent(self, _event):
        t = self._theme
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)

        if self._state == "done":
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(t.S_GREEN))
            p.drawEllipse(rect)
            # checkmark
            pen = QPen(QColor("#0F1620"))
            pen.setWidthF(2.0)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            cx, cy = self.width() / 2, self.height() / 2
            p.drawPolyline([
                self._pt(cx - 3, cy + 0.5),
                self._pt(cx - 1, cy + 2.5),
                self._pt(cx + 3, cy - 1.5),
            ])

        elif self._state == "running":
            pen = QPen(QColor(t.S_ACCENT))
            pen.setWidthF(2.0)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(rect)
            inner = rect.adjusted(3, 3, -3, -3)
            color = QColor(t.S_ACCENT)
            color.setAlphaF(self._pulse)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color)
            p.drawEllipse(inner)

        elif self._state == "paused":
            pen = QPen(QColor(t.S_YELLOW))
            pen.setWidthF(2.0)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(rect)
            # two vertical bars inside
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(t.S_YELLOW))
            cx, cy = self.width() / 2, self.height() / 2
            bar_w, bar_h = 1.5, 6.0
            from PySide6.QtCore import QRectF
            p.drawRect(QRectF(cx - 2.0, cy - bar_h / 2, bar_w, bar_h))
            p.drawRect(QRectF(cx + 0.5, cy - bar_h / 2, bar_w, bar_h))

        else:  # idle
            pen = QPen(QColor(t.S_DIM))
            pen.setWidthF(1.5)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            color = pen.color()
            color.setAlphaF(0.7)
            pen.setColor(color)
            p.setPen(pen)
            p.drawEllipse(rect)

        p.end()

    @staticmethod
    def _pt(x, y):
        from PySide6.QtCore import QPointF
        return QPointF(x, y)
