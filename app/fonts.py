"""
Font loading. Registers bundled Inter (UI) and JetBrains Mono (numeric labels)
with Qt so the rest of the app can refer to them by family name.

Call `load_fonts()` once after QApplication is created and before any UI is built.
"""
from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtGui import QFontDatabase, QFont

ASSETS_DIR = Path(__file__).parent / "assets" / "fonts"

INTER_FAMILY = "Inter 18pt"
MONO_FAMILY = "JetBrains Mono"

# Files to register. Static cuts (not the variable font) for predictable Tk-style usage.
FONT_FILES = [
    "Inter_18pt-Regular.ttf",
    "Inter_18pt-Medium.ttf",
    "Inter_18pt-SemiBold.ttf",
    "Inter_18pt-Bold.ttf",
    "JetBrainsMono-Regular.ttf",
    "JetBrainsMono-Medium.ttf",
    "JetBrainsMono-Bold.ttf",
]


def load_fonts() -> None:
    """Register all bundled fonts with QFontDatabase."""
    missing = []
    for fname in FONT_FILES:
        path = ASSETS_DIR / fname
        if not path.exists():
            missing.append(fname)
            continue
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id < 0:
            missing.append(fname)
    if missing:
        raise RuntimeError(f"Failed to load fonts: {missing}")


def ui(size: int = 13, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """Inter font at given size/weight — for any UI text."""
    f = QFont(INTER_FAMILY, size)
    f.setWeight(weight)
    f.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    return f


def mono(size: int = 12, weight: QFont.Weight = QFont.Weight.Medium) -> QFont:
    """JetBrains Mono — for ALL numeric labels (timer, durations, percentages)."""
    f = QFont(MONO_FAMILY, size)
    f.setWeight(weight)
    f.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    return f
