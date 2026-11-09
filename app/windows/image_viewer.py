"""
ImageViewer — modal dialog that shows a single image full-size.

Closes on Esc, on the system close button, or on a click anywhere on the image.
The window is sized to fit the image, capped at 90% of the available screen.
"""
from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QKeyEvent, QPixmap, QMouseEvent
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout


class ImageViewer(QDialog):
    BG = "#111111"

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(Path(image_path).name)
        self.setStyleSheet(f"QDialog {{ background-color: {self.BG}; }}")

        pixmap = QPixmap(image_path) if os.path.exists(image_path) else QPixmap()
        if pixmap.isNull():
            self._build_error_state()
            return

        # Cap rendered size to 90% of available screen (leaves room for title bar).
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            geo = screen.availableGeometry()
            max_w = int(geo.width() * 0.9)
            max_h = int(geo.height() * 0.9)
            if pixmap.width() > max_w or pixmap.height() > max_h:
                pixmap = pixmap.scaled(
                    max_w, max_h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel()
        self._label.setPixmap(pixmap)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(f"background-color: {self.BG};")
        self._label.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._label)

        self.resize(pixmap.width(), pixmap.height())

    def _build_error_state(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        msg = QLabel("Image cannot be displayed (file missing or unreadable).")
        msg.setStyleSheet("color: #F38BA8;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)
        self.resize(420, 120)

    # --- Close shortcuts ---

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.close()
            return
        super().mousePressEvent(event)
