"""
Color tokens and theme definitions.

Token names match DESIGN_BRIEF.md §5 and the designer's tokens.jsx.
Active theme is Gunmetal — Silver / Pewter / Paper are placeholders for later.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    is_dark: bool

    # Surfaces
    S_BG: str           # app background
    S_BG_DEEP: str      # title bar / footer (deeper bg)
    S_SURFACE: str      # cards, inputs
    S_ACTIVE: str       # active card base (gradient overlay on top)
    S_BORDER: str       # 1px borders

    # Text
    S_FG: str           # primary text
    S_TEXT_MUTED: str   # secondary text
    S_DIM: str          # dimmed text / placeholders

    # Accent
    S_ACCENT: str       # accent / running — same as S_RED in Gunmetal
    S_ACCENT_HOVER: str

    # Semantic
    S_GREEN: str        # START / break / done
    S_RED: str          # STOP / DELETE
    S_YELLOW: str       # DONE / paused
    URL_LINK: str

    # Buttons
    BTN_TEXT_ON_ACCENT: str

    # Focus overlay
    DEFAULT_FOCUS_BG: str
    DEFAULT_FOCUS_FG: str
    S_OVERLAY_BTN: str          # white α14 on red gradient
    S_OVERLAY_BTN_HOVER: str    # white α22
    S_OVERLAY_BTN_BORDER: str   # white α18


GUNMETAL = Theme(
    name="gunmetal",
    is_dark=True,

    S_BG="#1F2731",
    S_BG_DEEP="#161D26",
    S_SURFACE="#33404E",
    S_ACTIVE="#3D4B5B",
    S_BORDER="#2A3540",

    S_FG="#DBE3EC",
    S_TEXT_MUTED="#94A3B3",
    S_DIM="#7B8A9D",

    S_ACCENT="#EF4444",
    S_ACCENT_HOVER="#F87171",

    S_GREEN="#34D399",
    S_RED="#EF4444",
    S_YELLOW="#FBBF24",
    URL_LINK="#7DD3FC",

    BTN_TEXT_ON_ACCENT="#0F1620",

    DEFAULT_FOCUS_BG="#DC2626",
    DEFAULT_FOCUS_FG="#FFFFFF",
    S_OVERLAY_BTN="rgba(255,255,255,0.14)",
    S_OVERLAY_BTN_HOVER="rgba(255,255,255,0.22)",
    S_OVERLAY_BTN_BORDER="rgba(255,255,255,0.18)",
)


# Placeholders — populated when we ship a theme switcher.
# Source: Design/Focus App/components/MainWindow.jsx (THEMES dict).
THEMES: dict[str, Theme] = {
    "gunmetal": GUNMETAL,
    # "silver": Theme(...),
    # "pewter": Theme(...),
    # "paper":  Theme(...),
}

ACTIVE_THEME_NAME = "gunmetal"


def active_theme() -> Theme:
    return THEMES[ACTIVE_THEME_NAME]
