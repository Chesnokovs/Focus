"""
DescriptionEdit — multiline text editor that intercepts:
  • Ctrl+V image paste — saves clipboard image to disk, emits `imagesAdded`.
  • Drag-drop of image files — emits `imagesAdded` with their paths.
  • URL highlighting — http(s) links are coloured + underlined.
  • Ctrl+Click on a URL opens it in the default browser.

Plain text paste behaves normally.
"""
from __future__ import annotations

import os
import re
import uuid
import webbrowser
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import (
    QImage, QDragEnterEvent, QDragMoveEvent, QDropEvent,
    QKeyEvent, QKeySequence, QMouseEvent,
    QSyntaxHighlighter, QTextCharFormat, QColor,
)
from PySide6.QtWidgets import QPlainTextEdit, QApplication

from app import themes
from app.models import images_dir


IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

# Match http(s) URLs up to the next whitespace/quote/angle bracket.
URL_RE = re.compile(r'https?://[^\s<>\'"]+')
# Strip these trailing characters before opening — they're usually sentence
# punctuation, not part of the URL.
_URL_TRAILING_TRIM = ".,;:!?)]}>\"'"


def clean_url(raw: str) -> str:
    while raw and raw[-1] in _URL_TRAILING_TRIM:
        raw = raw[:-1]
    return raw


def collect_image_paths(mime: QMimeData) -> list[str]:
    """Return local image file paths from a MIME blob's URL list."""
    if not mime.hasUrls():
        return []
    out: list[str] = []
    for url in mime.urls():
        if not url.isLocalFile():
            continue
        local = url.toLocalFile()
        if Path(local).suffix.lower() in IMG_EXTS:
            out.append(local)
    return out


class _UrlHighlighter(QSyntaxHighlighter):
    """Colours and underlines http(s) URLs in the document."""
    def __init__(self, document, *, color: str):
        super().__init__(document)
        self._fmt = QTextCharFormat()
        self._fmt.setForeground(QColor(color))
        self._fmt.setFontUnderline(True)

    def highlightBlock(self, text: str) -> None:
        for m in URL_RE.finditer(text):
            self.setFormat(m.start(), m.end() - m.start(), self._fmt)


def save_clipboard_image(img: QImage) -> str | None:
    """Persist a clipboard QImage to focus_images/ and return its path."""
    if img.isNull():
        return None
    try:
        d = images_dir()
        name = f"{uuid.uuid4().hex[:12]}.png"
        path = os.path.join(d, name)
        if img.save(path, "PNG"):
            return path
    except OSError:
        pass
    return None


class DescriptionEdit(QPlainTextEdit):
    imagesAdded = Signal(list)  # list[str]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)  # so we can update cursor on hover
        self._highlighter = _UrlHighlighter(
            self.document(),
            color=themes.active_theme().URL_LINK,
        )

    # --- URL hover & Ctrl+Click ---

    def _url_at(self, pos) -> str | None:
        """Return the URL string under the given viewport-relative position, or None."""
        cursor = self.cursorForPosition(pos)
        block = cursor.block()
        text = block.text()
        offset = cursor.position() - block.position()
        for m in URL_RE.finditer(text):
            if m.start() <= offset <= m.end():
                return clean_url(m.group())
        return None

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        # Pointing-hand cursor when over a URL — plain hover, no modifier needed.
        if self._url_at(event.position().toPoint()):
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            url = self._url_at(event.position().toPoint())
            if url:
                webbrowser.open(url)
                event.accept()
                return
        super().mouseReleaseEvent(event)

    # --- Paste (Ctrl+V) ---
    # We intercept the keypress (rather than `insertFromMimeData`) and use
    # QClipboard.image() directly. The MIME-based path can segfault on some
    # clipboard formats when QVariant unwrap is fed into QImage(...).
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.matches(QKeySequence.StandardKey.Paste):
            clipboard = QApplication.clipboard()
            img = clipboard.image()
            if not img.isNull():
                path = save_clipboard_image(img)
                if path:
                    self.imagesAdded.emit([path])
                    event.accept()
                    return
            # No image on clipboard — fall through to normal text paste.
        super().keyPressEvent(event)

    # --- Drag and drop of image files ---
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if collect_image_paths(event.mimeData()):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if collect_image_paths(event.mimeData()):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        paths = collect_image_paths(event.mimeData())
        if paths:
            self.imagesAdded.emit(paths)
            event.acceptProposedAction()
            return
        super().dropEvent(event)
