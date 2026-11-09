"""
Entry point for the Focus App (PySide6).

    python -m app.main
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMessageBox

from app import fonts
from app.models import Store, is_frozen, log_path
from app.windows.main_window import MainWindow

log = logging.getLogger("focus")


def _setup_logging() -> None:
    """Log to a file: the windowed .exe has no console to print errors to."""
    try:
        handler = RotatingFileHandler(
            log_path(), maxBytes=256 * 1024, backupCount=1, encoding="utf-8"
        )
    except OSError:
        return
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)

    previous_hook = sys.excepthook

    def hook(exc_type, exc, tb):
        log.error("Unhandled exception", exc_info=(exc_type, exc, tb))
        previous_hook(exc_type, exc, tb)

    # PySide routes exceptions raised inside slots through sys.excepthook.
    sys.excepthook = hook


def _instance_key() -> str:
    """Pipe name shared by all launches of this app by this user."""
    user = os.environ.get("USERNAME") or os.environ.get("USER") or "user"
    # A dev run from source must not be swallowed by an installed .exe.
    return f"FocusApp-{user}" + ("" if is_frozen() else "-dev")


# Must match AppMutex in installer/FocusApp.iss.
APP_MUTEX = "FocusAppRunningMutex"


def _hold_app_mutex():
    """Create the named mutex the installer looks for.

    Setup and uninstall check it to ask the user to quit Focus first — a
    copy hidden in the tray would otherwise keep the program files locked.
    Windows releases it when the process ends.
    """
    if not is_frozen() or sys.platform != "win32":
        return None
    import ctypes
    return ctypes.windll.kernel32.CreateMutexW(None, False, APP_MUTEX)


def _activate_running_instance(key: str) -> bool:
    """Ask an already running copy to show its window. True if one answered."""
    sock = QLocalSocket()
    sock.connectToServer(key)
    if not sock.waitForConnected(300):
        return False
    sock.write(b"show")
    sock.waitForBytesWritten(300)
    sock.disconnectFromServer()
    return True


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Focus App")
    app_mutex = _hold_app_mutex()  # noqa: F841 — held for the process lifetime

    # With the window hidden in the tray, launching the .exe again must bring
    # that window back — two copies would overwrite each other's data file.
    key = _instance_key()
    if _activate_running_instance(key):
        return 0
    server = QLocalServer()
    server.listen(key)

    _setup_logging()

    # The window hides to the tray, so "no visible windows" is not "quit".
    app.setQuitOnLastWindowClosed(False)

    icon_path = Path(__file__).parent / "assets" / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    fonts.load_fonts()

    store = Store.load()
    win = MainWindow(store)

    def on_second_launch() -> None:
        while server.hasPendingConnections():
            conn = server.nextPendingConnection()
            conn.disconnectFromServer()
            conn.deleteLater()
        win.show_from_tray()

    server.newConnection.connect(on_second_launch)
    # Windows logoff / shutdown: save, and let the window actually close.
    app.commitDataRequest.connect(lambda *_: win.prepare_for_session_end())
    app.aboutToQuit.connect(win.flush)

    # "--minimized" is how the autostart entry launches us: straight into the
    # tray. Without a tray there would be no way to reach a hidden window.
    start_hidden = "--minimized" in sys.argv[1:] and win.has_tray
    if store.load_warning:
        log.warning(store.load_warning)
        start_hidden = False
    if not start_hidden:
        win.show()
    if store.load_warning:
        QMessageBox.warning(win, "Focus", store.load_warning)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
