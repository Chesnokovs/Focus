"""
Render the user-provided Icon.svg (red gradient square with white "F")
into a multi-resolution Windows .ico file used by:
  - PyInstaller's --icon flag (sets the .exe icon in Explorer / taskbar)
  - QApplication.setWindowIcon() at runtime (sets the title-bar icon)

Output: app/assets/icon.ico
"""
import os
import sys
from io import BytesIO
from pathlib import Path

from PySide6.QtCore import Qt, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QImage, QPainter, QGuiApplication
from PySide6.QtSvg import QSvgRenderer
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "Icon.svg"
DST = Path(__file__).parent / "icon.ico"

ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def render_svg_png(svg_bytes: bytes, size: int) -> bytes:
    """Render svg at exactly `size`×`size` and return PNG bytes."""
    renderer = QSvgRenderer(QByteArray(svg_bytes))
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    renderer.render(painter)
    painter.end()

    buf = QByteArray()
    qbuf = QBuffer(buf)
    qbuf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(qbuf, "PNG")
    qbuf.close()
    return bytes(buf)


def main() -> int:
    if not SRC.exists():
        print(f"ERROR: source SVG not found: {SRC}")
        return 1

    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    svg_bytes = SRC.read_bytes()

    # Render the largest size, let Pillow generate the smaller ones inside ICO.
    png_data = render_svg_png(svg_bytes, 256)
    src = Image.open(BytesIO(png_data)).convert("RGBA")

    src.save(DST, format="ICO", sizes=[(s, s) for s in ICO_SIZES])
    print(f"Wrote {DST}  ({len(ICO_SIZES)} sizes: {ICO_SIZES})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
