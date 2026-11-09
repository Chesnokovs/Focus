# Focus App

A Windows desktop app for staying focused on one task at a time: a task list, a Pomodoro timer, and a small always-on-top window that keeps the current task in front of you.

![Focus App icon](Icon.svg)

## Contents

1. [Install](#install)
2. [Features](#features)
3. [Where your data lives](#where-your-data-lives)
4. [Project layout](#project-layout)
5. [Building the installer](#building-the-installer)
6. [Running from source](#running-from-source)
7. [Developer notes](#developer-notes)
8. [Designer notes](#designer-notes)
9. [Third-party components](#third-party-components)
10. [Version history](#version-history)

## Install

Run `FocusApp-Setup-<version>.exe` and follow the wizard.

- **Requirements:** 64-bit Windows 10 (version 1809 or later) or Windows 11. Nothing else needs to be installed — Python, Qt and the Microsoft C++ runtime are all inside the app.
- **No administrator rights needed.** By default the app installs for the current user into `%LOCALAPPDATA%\Programs\Focus`. The wizard also offers "install for all users" if you have administrator rights.
- **Options in the wizard:** a desktop shortcut, and starting Focus automatically (hidden in the tray) when you sign in to Windows.
- **Upgrading:** run a newer installer over the old one. If Focus is running, the installer asks you to quit it first (tray icon → **Quit**).
- **Uninstalling:** *Settings → Apps → Installed apps → Focus → Uninstall*. Your tasks are kept (see [Where your data lives](#where-your-data-lives)).

> **"Windows protected your PC".** The installer is not code-signed, so Microsoft SmartScreen may show this warning on a PC that has not seen the file before. Click **More info → Run anyway**. Removing the warning requires a paid code-signing certificate.

## Features

- Task list with inline editing of the name and description.
- Links in the description are highlighted; **Ctrl+Click** opens one in the browser (a plain click places the caret).
- Attach images to a task with the **+ Image** button, with **Ctrl+V** from the clipboard, or by dragging files from Explorer. The image is copied into the data folder, so the original can be deleted. Click a thumbnail to view it full size.
- Four task states: idle / running / paused / done. A done task can be put back to work (**Reopen**); any task can be removed (**Delete** in the expanded card).
- Pomodoro timer — 25 minutes of work, 5 minutes of break by default. Phases switch automatically, with a sound and a notification.
- A floating always-on-top window with the task title and the timer. Double-click it to open the main window.
- **System tray.** Minimising or closing the main window hides it to the tray while the timer keeps running. Click the tray icon to bring the window back; right-click for Pause/Resume and **Quit** — the only way to exit the app.
- Launching the app again does not start a second copy; it shows the window of the one already running.
- Daily statistics in the footer: **Today** (total focus time today) and **Streak** (consecutive days with at least one second of focus).
- Every change is saved to disk automatically.

## Where your data lives

The installed app keeps everything in `%APPDATA%\FocusApp\` (paste that into Explorer's address bar):

- **`focus_tasks.json`** — all tasks, settings and daily statistics. A single file; copy it to back up.
- **`focus_tasks.json.bak`** — a copy from the previous successful launch.
- **`focus_images\`** — images attached to tasks.
- **`focus.log`** — error log.

The folder is independent of where the program is installed: upgrading, reinstalling or uninstalling the app does not touch it. To remove your data as well, delete the folder by hand.

**Coming from version 2.0 or earlier.** Those versions were a single portable `FocusApp.exe` that kept its data next to itself. When version 2.1+ is started from that same folder, it copies `focus_tasks.json` and `focus_images\` into `%APPDATA%\FocusApp\` once; the old files are left in place as a backup and are no longer read. If you install with the installer instead, copy those two items into `%APPDATA%\FocusApp\` yourself before the first launch.

## Project layout

```
Focus_App/
├── app/                          # Application source (PySide6)
│   ├── __init__.py               # __version__ — the single source of the version
│   ├── main.py                   # entry point: single instance, logging, startup
│   ├── themes.py                 # colour themes
│   ├── fonts.py                  # loads Inter / JetBrains Mono
│   ├── icons.py                  # PNG icon registry
│   ├── models.py                 # Task, Stats, Settings, Store (JSON persistence)
│   ├── windows/                  # top-level windows
│   │   ├── main_window.py        # main window: task list, timer, tray icon
│   │   ├── focus_window.py       # floating always-on-top window
│   │   └── image_viewer.py       # full-size image viewer
│   ├── widgets/                  # reusable widgets
│   │   ├── task_card.py          # task card (4 states, expandable panel)
│   │   ├── state_indicator.py    # pulsing state dot
│   │   ├── action_button.py      # action buttons, 5 variants (start/done/stop/...)
│   │   ├── circular_progress.py  # progress ring for FocusWindow
│   │   ├── pulsing_dot.py        # small pulsing dot in the overlay header
│   │   ├── elided_label.py       # one-line text that shows "…" instead of stretching the window
│   │   └── description_edit.py   # text area with link highlighting and image paste/drop
│   └── assets/
│       ├── fonts/                # 7 .ttf fonts (Inter + JetBrains Mono)
│       ├── icons/                # PNG @2x icons
│       ├── icon.ico              # application icon (multi-resolution)
│       ├── _build_icons.py       # re-renders the UI icons from inline SVG
│       └── _build_app_icon.py    # re-renders icon.ico from Icon.svg
│
├── installer/
│   └── FocusApp.iss              # Inno Setup script
│
├── Design/                       # Designer hand-off (live reference)
│   └── Focus App/                # JSX sources + specifications
│       ├── Focus App Spec.html   # readable design-system spec (open in a browser)
│       ├── Focus App.html        # design canvas with the alternative themes
│       ├── components/           # reference React components, themes in a THEMES dict
│       └── spec/                 # JSX modules of the spec
│
├── legacy/                       # Archive: the old CustomTkinter version
│   └── focus_app.py              # single file, before the move to PySide6
│
├── build/                        # Build intermediates (not in git)
├── dist/                         # Build output: the installer (not in git)
│
├── DESIGN_BRIEF.md               # redesign brief v3 (historical context)
├── FocusApp.spec                 # PyInstaller recipe
├── Icon.svg                      # source of the application icon
├── README.md                     # this file
├── build.bat                     # builds the app and the installer
├── run.py                        # entry point used by PyInstaller
└── requirements.txt              # Python dependencies
```

## Building the installer

### Requirements

- Windows 10/11, 64-bit
- Python 3.10 or newer
- [Inno Setup 6](https://jrsoftware.org/isdl.php)

### Build

Double-click `build.bat`, or from a terminal:

```cmd
build.bat
```

The script:

1. creates a private `.venv` and installs the packages from `requirements.txt` into it (nothing is installed system-wide);
2. runs PyInstaller with `FocusApp.spec` → `build\app\FocusApp\` (the app as a folder: `FocusApp.exe` + `_internal\`);
3. runs Inno Setup with `installer\FocusApp.iss` → **`dist\FocusApp-Setup-<version>.exe`**.

The whole build takes about a minute; the installer is roughly 27 MB.

### Releasing a new version

Change `__version__` in [app/__init__.py](app/__init__.py) and run `build.bat`. The version is stamped into `FocusApp.exe`, shown in *Installed apps*, and used in the installer's file name. Do not change `AppId` in `installer\FocusApp.iss` — it is what lets a new installer upgrade the previous version in place.

## Running from source

Without building anything:

```cmd
pip install -r requirements.txt
python -m app.main
```

In this mode the data is written to `focus_tasks.json` next to `app/` (the file is in `.gitignore`), not to `%APPDATA%\FocusApp\`, so experiments never touch your real tasks. For the same reason a run from source and the installed app count as different applications and can run side by side.

## Developer notes

### Extension points

| To add | Where | Notes |
|---|---|---|
| A new task field | [app/models.py](app/models.py) — `Task` | Update `from_dict()` so older JSON files still load |
| A new task state | [app/widgets/task_card.py](app/widgets/task_card.py) — `_state_name()` + `_build_action_strip()`, [app/widgets/state_indicator.py](app/widgets/state_indicator.py) | Add the new key and its indicator visual |
| A new action button | [app/widgets/action_button.py](app/widgets/action_button.py) | 5 variants exist; add a sixth in `_apply_style()` |
| A new sidebar / screen | a new file in [app/windows/](app/windows/) | Wire it up from `MainWindow._build_ui()` |
| Global hotkeys (Win32) | a new module `app/hotkeys.py` | Use `ctypes.windll.user32.RegisterHotKey` (legacy/focus_app.py has a working example) |
| Settings UI (popover) | a new file in [app/windows/](app/windows/) | Open it from MainWindow on a ⚙ click — put `IconButton("settings", ...)` back into `_build_header()` |
| A long break after N Pomodoro cycles | [app/windows/main_window.py](app/windows/main_window.py) — `_switch_phase()` | Currently a plain work↔break toggle with no cycle counter |
| A tray menu item | [app/windows/main_window.py](app/windows/main_window.py) — `_build_tray()` | |
| An installer option | [installer/FocusApp.iss](installer/FocusApp.iss) — `[Tasks]` | |

### Architecture decisions

- **PySide6 (Qt 6)** — all rendering goes through Qt. The first version used CustomTkinter (see legacy/) and hit the toolkit's performance ceiling: without double buffering, Tkinter flickers on every change.
- **The Store is the single source of truth.** Every mutation goes through a `MainWindow._on_*` handler, which then saves the JSON.
- **Incremental card updates.** When one task changes, only its card is rebuilt (`update_state` / `_refresh_card_expansion`). The whole list is rebuilt only on first paint.
- **A card's old widgets are removed with `deleteLater()`**, never destroyed on the spot. A rebuild is usually triggered by a child widget's own signal (a button click, the name field's `editingFinished`); destroying that widget inside its own signal leaves Qt running code on a freed object — this is what used to crash the app on rename.
- **The timer counts against the monotonic clock.** A `QTimer` fires every 250 ms and only checks how many whole seconds have passed (`_on_tick`), so a late or skipped timer event never loses time. A gap longer than a minute is treated as the PC sleeping and is not counted as focus.
- **FocusWindow is a passive view.** It does not count time itself; MainWindow pushes updates to it. This rules out drift between the two windows.
- **Saving is atomic**: the JSON is written to a temporary file that then replaces the real one via `os.replace`. Every successful launch refreshes `focus_tasks.json.bak`; an unreadable file is not overwritten but renamed to `focus_tasks.json.corrupt-<date>`, and the data is restored from the backup.
- **Periodic save every 30 seconds of timer time** — easy on the disk, little to lose in a crash. The app also saves on every task change, on quit, and when the Windows session ends.
- **Quitting goes through `MainWindow.quit_app()` only.** With a tray available, `closeEvent` hides the window; `QApplication.setQuitOnLastWindowClosed(False)` keeps Qt alive when no window is visible.
- **Single instance** — a `QLocalServer` in [app/main.py](app/main.py): a second launch connects to the first, asks it to show its window, and exits.
- **Installer awareness** — the built app holds a named mutex (`FocusAppRunningMutex`) that Inno Setup checks (`AppMutex`), so files are never replaced while a copy sits in the tray. `--minimized` on the command line (used by the autostart entry) starts the app hidden in the tray.
- **Folder build, not one-file.** PyInstaller's one-file mode unpacks the whole app to a temp folder on every launch; the folder build starts instantly, and the installer is what makes it a single download.
- **Log** — `focus.log` in the data folder (the windowed `.exe` has no console; unhandled exceptions are written there).

### Tests

There are no automated tests in the repository yet. They can be added with `pytest`: create a `QApplication([])` in a fixture, set `QT_QPA_PLATFORM=offscreen`, and point the app at a temporary folder by replacing `app.models.data_dir`. The system tray is not available on the `offscreen` platform — tray behaviour has to be tested on a real desktop.

## Designer notes

This section is for you if you want to **add a new theme / skin** (a light one, for example). The architecture is ready for theme switching; only the colours need to be added.

### Where the colours (palette) live

Every colour in the app is in one file: [app/themes.py](app/themes.py). It is Python, but the syntax is simple:

```python
GUNMETAL = Theme(
    name="gunmetal",
    is_dark=True,
    S_BG="#1F2731",        # main window background
    S_BG_DEEP="#161D26",   # title bar / footer (deeper)
    S_SURFACE="#33404E",   # cards, input fields
    S_ACTIVE="#3D4B5B",    # active task background (base under the gradient)
    S_BORDER="#2A3540",    # 1px borders
    S_FG="#DBE3EC",        # primary text
    S_TEXT_MUTED="#94A3B3",# secondary text
    S_DIM="#7B8A9D",       # dimmed text / placeholder
    S_ACCENT="#EF4444",    # red — running, Start buttons, FocusWindow
    S_ACCENT_HOVER="#F87171",
    S_GREEN="#34D399",     # done / break
    S_RED="#EF4444",       # stop / delete
    S_YELLOW="#FBBF24",    # paused
    URL_LINK="#7DD3FC",    # links in the description
    BTN_TEXT_ON_ACCENT="#0F1620",  # text on bright buttons
    DEFAULT_FOCUS_BG="#DC2626",     # FocusWindow background (always red in the current spec)
    DEFAULT_FOCUS_FG="#FFFFFF",
    S_OVERLAY_BTN="rgba(255,255,255,0.14)",          # buttons on the red overlay
    S_OVERLAY_BTN_HOVER="rgba(255,255,255,0.22)",
    S_OVERLAY_BTN_BORDER="rgba(255,255,255,0.18)",
)
```

### Adding a new theme (example: a light one)

1. **Open [app/themes.py](app/themes.py)** in any code editor (VS Code, Notepad++, Sublime).
2. **Copy the whole `GUNMETAL = Theme(...)` block** and rename it to `PAPER` (or any name you like).
3. **Fill in new hex values** for each token. The comment to the right of each line says what the token is for.
4. **Register the theme** in the `THEMES` dictionary:

   ```python
   THEMES: dict[str, Theme] = {
       "gunmetal": GUNMETAL,
       "paper": PAPER,            # ← added
   }
   ```

5. **Activate the theme** with one line:

   ```python
   ACTIVE_THEME_NAME = "paper"    # ← was "gunmetal"
   ```

6. **Run the app** and check the result.

You do not need to know any Python beyond what is shown above — these six steps are enough. No imports, classes or functions have to be touched.

### Where to see the alternative themes

The designer package already contains several ready-made themes in the JSX sources:

- **[Design/Focus App/components/MainWindow.jsx](Design/Focus%20App/components/MainWindow.jsx)** — see the `THEMES` object at the top of the file. It fully defines:
  - `graphite` (dark, the original)
  - `paper` (light, Things-like)
  - `cream` (warm cream)
  - `slate` (soft blue-gray)
  - `silver` (silvery, premium)
  - `gunmetal` (the active one)
  - `pewter` (warm steel)

- **[Design/Focus App/Focus App.html](Design/Focus%20App/Focus%20App.html)** — open it in a browser to see the themes side by side, as they look live.

To use a ready-made theme, just carry its colours over to Python. JSX → Python token mapping:

| JSX | Python |
|---|---|
| `chrome` | `S_BG_DEEP` |
| `bg0` | `S_BG` |
| `bg1` | `S_SURFACE` |
| `bg2` | `S_ACTIVE` |
| `border` | `S_BORDER` |
| `text0` | `S_FG` |
| `text1` | `S_FG` |
| `text2` | `S_TEXT_MUTED` |
| `text3` | `S_DIM` |
| `accent` | `S_ACCENT` |
| `accentSoft` | (not needed — computed as rgba 12% of S_ACCENT) |
| `success` | `S_GREEN` |
| `warn` | `S_YELLOW` |
| `footer` | `S_BG_DEEP` |

### Fonts

[app/assets/fonts/](app/assets/fonts/) holds 7 .ttf files:
- Inter (Regular / Medium / SemiBold / Bold)
- JetBrains Mono (Regular / Medium / Bold)

To use a different font:
1. Put the .ttf into `app/assets/fonts/`.
2. Open [app/fonts.py](app/fonts.py).
3. Add the file name to the `FONT_FILES` list.
4. Change `INTER_FAMILY` or `MONO_FAMILY` to the new font's family name (as Windows shows it).

The family name is in the .ttf file's properties (right-click → Properties → Details).

### Icons

[app/assets/icons/](app/assets/icons/) holds PNG @2x files. They are **not edited by hand** — a script generates them from inline SVG sources:

- **UI icons** (play, pause, stop, check, plus, settings, paperclip, upload, close, expand, chevron-right, chevron-down): the source is in [app/assets/_build_icons.py](app/assets/_build_icons.py). To change or add an icon, edit the SVG path in that file, then run:

  ```cmd
  python app/assets/_build_icons.py
  ```

- **Application icon** (shown on the .exe, in window title bars and in the tray): the source is [Icon.svg](Icon.svg) in the repository root. After changing the SVG, run:

  ```cmd
  python app/assets/_build_app_icon.py
  ```

  This updates `app/assets/icon.ico`. Then rebuild with `build.bat`.

### What NOT to do

- Do not edit files in `app/widgets/` or `app/windows/` — they hold logic and layout; they are reached through the tokens, not the other way round.
- Do not edit the PNG icons in a graphics editor — the next run of `_build_icons.py` overwrites them. Change the SVG source.
- Do not edit `app/assets/icon.ico` directly — it is generated from `Icon.svg`.

### If you need help

All colour tokens, sizes and states are recorded in [DESIGN_BRIEF.md](DESIGN_BRIEF.md) v3 — the specification for the current redesign. It can serve as the basis for a new theme: replace only `§5 Design tokens`.

## Third-party components

The installer bundles these components, each under its own licence:

| Component | Licence |
|---|---|
| [Qt 6](https://www.qt.io/) and [PySide6](https://doc.qt.io/qtforpython-6/) | LGPL v3 |
| [Python](https://www.python.org/) | PSF License |
| [Inter](https://github.com/rsms/inter) font | SIL Open Font License 1.1 |
| [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono) font | SIL Open Font License 1.1 |

## Version history

- **v2.1** (current) — system tray, single instance, installer; data moved to `%APPDATA%\FocusApp` with atomic saves and backups; rename crash and long-title layout fixed.
- **v2** — PySide6, the Gunmetal design language, extended functionality (paused state, footer with streak, always-on-top FocusWindow).
- **v1** — CustomTkinter (see [legacy/focus_app.py](legacy/focus_app.py)). A simple UI that hit the toolkit's performance ceiling, hence the move.
