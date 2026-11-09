"""
Generate PNG icons from the designer's SVG sources in
Design/Focus App/components/Icon.jsx. Run once after the design package
is updated. Output: app/assets/icons/<name>@2x.png (32x32, white stroke).

Uses PySide6's QSvgRenderer — no native deps required.
"""
import os
import sys

from PySide6.QtCore import Qt, QByteArray
from PySide6.QtGui import QImage, QPainter, QGuiApplication
from PySide6.QtSvg import QSvgRenderer

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
os.makedirs(OUT_DIR, exist_ok=True)

# Extracted from Design/Focus App/components/Icon.jsx — verbatim.
# 16x16 viewBox. Render at 2x (32x32).
ICONS = {
    "play":          ('<path d="M5 3l8 5-8 5V3z" fill="{c}" stroke="none"/>',          "fill"),
    "pause":         ('<path d="M5 3v10M11 3v10"/>',                                   "stroke"),
    "stop":          ('<rect x="4" y="4" width="8" height="8" rx="1" fill="{c}" stroke="none"/>', "fill"),
    "check":         ('<path d="M3 8l3 3 7-7"/>',                                      "stroke"),
    "plus":          ('<path d="M8 3v10M3 8h10"/>',                                    "stroke"),
    "settings":      ('<circle cx="8" cy="8" r="2"/>'
                      '<path d="M8 1v2M8 13v2M3.5 3.5l1.4 1.4M11.1 11.1l1.4 1.4'
                      'M1 8h2M13 8h2M3.5 12.5l1.4-1.4M11.1 4.9l1.4-1.4"/>',            "stroke"),
    "paperclip":     ('<path d="M11 5L6 10a2 2 0 102.8 2.8L13 8.5a3.5 3.5 0 10-5-5L4 7.5"/>', "stroke"),
    "upload":        ('<path d="M8 11V3M4 7l4-4 4 4M3 13h10"/>',                       "stroke"),
    "close":         ('<path d="M3 3l10 10M13 3L3 13"/>',                              "stroke"),
    "expand":        ('<path d="M3 3h4M3 3v4M13 13h-4M13 13v-4"/>',                    "stroke"),
    "chevron-right": ('<path d="M6 3l5 5-5 5"/>',                                      "stroke"),
    "chevron-down":  ('<path d="M3 6l5 5 5-5"/>',                                      "stroke"),
}

# Two color variants — designer uses white on red overlay, S_FG (#DBE3EC) on dark UI.
COLORS = {
    "":      "#DBE3EC",  # default — main UI text color
    "white": "#FFFFFF",  # for buttons on accent / overlay
}


def build_svg(body: str, color: str, mode: str) -> bytes:
    body = body.replace("{c}", color)
    if mode == "stroke":
        attrs = (f'fill="none" stroke="{color}" stroke-width="2" '
                 f'stroke-linecap="round" stroke-linejoin="round"')
    else:
        attrs = ''
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" '
        f'width="16" height="16" {attrs}>{body}</svg>'
    ).encode("utf-8")


def render_to_png(svg_bytes: bytes, out_path: str, size: int = 32):
    renderer = QSvgRenderer(QByteArray(svg_bytes))
    if not renderer.isValid():
        raise RuntimeError(f"Invalid SVG for {out_path}")
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    renderer.render(painter)
    painter.end()
    img.save(out_path, "PNG")


def build_halo_running() -> bytes:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" '
        'width="32" height="32">'
        '<defs>'
        '<radialGradient id="g" cx="50%" cy="50%" r="50%">'
        '<stop offset="20%" stop-color="#EF4444" stop-opacity="1"/>'
        '<stop offset="60%" stop-color="#EF4444" stop-opacity="0.35"/>'
        '<stop offset="100%" stop-color="#EF4444" stop-opacity="0"/>'
        '</radialGradient>'
        '</defs>'
        '<circle cx="16" cy="16" r="14" fill="url(#g)"/>'
        '<circle cx="16" cy="16" r="5" fill="#EF4444"/>'
        '</svg>'
    ).encode("utf-8")


def build_halo_idle() -> bytes:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" '
        'width="32" height="32">'
        '<circle cx="16" cy="16" r="5" fill="none" '
        'stroke="#7B8A9D" stroke-width="2"/>'
        '</svg>'
    ).encode("utf-8")


def main():
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    print(f"Rendering {len(ICONS)} icons x {len(COLORS)} colors -> {OUT_DIR}")
    for name, (body, mode) in ICONS.items():
        for variant, hex_value in COLORS.items():
            svg = build_svg(body, hex_value, mode)
            suffix = f"-{variant}" if variant else ""
            out = os.path.join(OUT_DIR, f"{name}{suffix}@2x.png")
            render_to_png(svg, out, 32)
            print(f"  {os.path.basename(out)}")
    render_to_png(build_halo_running(), os.path.join(OUT_DIR, "dot-running@2x.png"), 32)
    render_to_png(build_halo_idle(), os.path.join(OUT_DIR, "dot-idle@2x.png"), 32)
    print("  dot-running@2x.png")
    print("  dot-idle@2x.png")


if __name__ == "__main__":
    main()
