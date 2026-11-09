"""
Icon registry. Loads PNG @2x icons from app/assets/icons/ and serves
them as QIcon / QPixmap with proper HiDPI handling.

Designer ships 32×32 (2x of 16). Qt scales down for 1x displays.
"""
from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap

ICONS_DIR = Path(__file__).parent / "assets" / "icons"

# Cache loaded pixmaps to avoid repeated disk reads.
_cache: dict[str, QPixmap] = {}


def pixmap(name: str, *, white: bool = False) -> QPixmap:
    """Load an icon as QPixmap. `white=True` picks the white-on-color variant."""
    suffix = "-white" if white else ""
    key = f"{name}{suffix}"
    if key in _cache:
        return _cache[key]
    path = ICONS_DIR / f"{name}{suffix}@2x.png"
    pm = QPixmap(str(path))
    if pm.isNull():
        # Quietly fall back to a 1x1 transparent pixmap rather than crash —
        # missing icons should be visible but not fatal.
        pm = QPixmap(2, 2)
        pm.fill(Qt.GlobalColor.transparent)
    pm.setDevicePixelRatio(2.0)  # mark as @2x for HiDPI scaling
    _cache[key] = pm
    return pm


def icon(name: str, *, white: bool = False) -> QIcon:
    return QIcon(pixmap(name, white=white))


def icon_size_logical(px: int) -> QSize:
    """Helper to express icon size in logical (1x) pixels."""
    return QSize(px, px)
