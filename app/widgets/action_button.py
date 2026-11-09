"""
ActionButton — small action button used on task cards (Start / Pause / Stop / Done /
Resume / Delete). 5 visual variants matching designer's mockup:

    primary : red bg, white text, no border       (Start / Resume)
    yellow  : yellow bg, dark text                (Done — bright)
    warn    : translucent yellow bg, yellow text  (Pause — soft)
    stop    : surface bg, primary text            (Stop)
    ghost   : transparent bg, dim text, border    (Done — quiet, Delete)

Hover: background brightens by ~+12%, simulated via a hover-color in the QSS.
Pressed: background dims by ~-8%.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QPushButton

from app import fonts, icons, themes


def _shift(hex_color: str, amount: float) -> str:
    """Lighten (amount > 0) or darken (amount < 0) a #RRGGBB color."""
    c = QColor(hex_color)
    h, s, l, a = c.getHslF()
    l = max(0.0, min(1.0, l + amount))
    c.setHslF(h, s, l, a)
    return c.name(QColor.NameFormat.HexRgb)


class ActionButton(QPushButton):
    HEIGHT = 28

    def __init__(self, variant: str, icon_name: str, label: str = "",
                 *, theme: themes.Theme | None = None):
        super().__init__()
        self._variant = variant
        self._theme = theme or themes.active_theme()
        self._icon_name = icon_name
        self._has_label = bool(label)

        self.setText(f"  {label}" if label else "")
        self.setFont(fonts.ui(12, QFont.Weight.DemiBold))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(self.HEIGHT)
        if not self._has_label:
            self.setFixedWidth(self.HEIGHT)

        self._apply_style()
        self._apply_icon()

    def _apply_icon(self):
        """Choose icon color variant (white on dark/colored bg, default on light)."""
        # primary, yellow, stop, warn → white-ish foreground; ghost → default fg
        white_variants = {"primary", "yellow", "stop", "warn"}
        use_white = self._variant in white_variants
        # 'yellow' has dark text per spec, so icon should also be dark — use default
        if self._variant == "yellow":
            use_white = False
        self.setIcon(icons.icon(self._icon_name, white=use_white))
        self.setIconSize(QSize(11, 11))

    def _apply_style(self):
        t = self._theme
        v = self._variant

        if v == "primary":
            bg, fg, border = t.S_ACCENT, "#FFFFFF", "transparent"
            hover = t.S_ACCENT_HOVER
        elif v == "yellow":
            bg, fg, border = t.S_YELLOW, t.BTN_TEXT_ON_ACCENT, "transparent"
            hover = _shift(bg, +0.06)
        elif v == "warn":
            # translucent yellow tint; rgba in QSS works fine
            bg = "rgba(251, 191, 36, 0.15)"
            hover = "rgba(251, 191, 36, 0.25)"
            fg = t.S_YELLOW
            border = "rgba(251, 191, 36, 0.40)"
        elif v == "stop":
            bg, fg, border = t.S_BG, t.S_FG, t.S_BORDER
            hover = _shift(bg, +0.05)
        elif v == "ghost":
            bg, fg, border = "transparent", t.S_DIM, t.S_BORDER
            hover = t.S_SURFACE
        else:
            raise ValueError(f"Unknown ActionButton variant: {v}")

        # Pressed shade — slightly darker than normal bg.
        pressed = _shift(bg, -0.04) if bg.startswith("#") else bg

        pad_x = 12 if self._has_label else 0
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 0 {pad_x}px;
                text-align: left;
            }}
            QPushButton:hover {{ background-color: {hover}; }}
            QPushButton:pressed {{ background-color: {pressed}; }}
        """)
