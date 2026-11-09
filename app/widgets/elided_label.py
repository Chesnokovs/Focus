"""
ElidedLabel — single-line text that shrinks with an ellipsis instead of
forcing its parent wider. A plain QLabel's minimum width is its full text,
which made long task names push the action buttons out of the window.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget


class ElidedLabel(QWidget):
    def __init__(self, text: str = "", *, font: QFont, color: str):
        super().__init__()
        self._text = text
        self._color = QColor(color)
        self.setFont(font)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def text(self) -> str:
        return self._text

    def setText(self, text: str) -> None:
        if text == self._text:
            return
        self._text = text
        self.updateGeometry()
        self._sync_tooltip()
        self.update()

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        return QSize(fm.horizontalAdvance(self._text) + 2, fm.height())

    def minimumSizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        return QSize(fm.horizontalAdvance("…") * 3, fm.height())

    def _is_elided(self) -> bool:
        return QFontMetrics(self.font()).horizontalAdvance(self._text) > self.width()

    def _sync_tooltip(self) -> None:
        # The full text is only worth a tooltip when part of it is hidden.
        self.setToolTip(self._text if self._is_elided() else "")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._sync_tooltip()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setFont(self.font())
        p.setPen(self._color)
        fm = QFontMetrics(self.font())
        shown = fm.elidedText(self._text, Qt.TextElideMode.ElideRight, self.width())
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, shown)
        p.end()
