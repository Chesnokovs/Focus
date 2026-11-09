# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller recipe for Focus App. Run through build.bat.

Produces a folder build (FocusApp.exe + _internal\) that the installer
packs. A folder starts instantly; a one-file .exe unpacks ~50 MB to a temp
directory on every launch.
"""
import os
import sys

from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo, StringFileInfo, StringStruct, StringTable,
    VarFileInfo, VarStruct, VSVersionInfo,
)

sys.path.insert(0, SPECPATH)
from app import __version__  # noqa: E402

_parts = tuple(int(p) for p in __version__.split(".")) + (0,) * 4
_ver = _parts[:4]

# Shown in Explorer's file properties.
version_info = VSVersionInfo(
    ffi=FixedFileInfo(filevers=_ver, prodvers=_ver),
    kids=[
        StringFileInfo([StringTable("040904B0", [
            StringStruct("CompanyName", "Chesnokovs"),
            StringStruct("FileDescription", "Focus"),
            StringStruct("FileVersion", __version__),
            StringStruct("InternalName", "FocusApp"),
            StringStruct("OriginalFilename", "FocusApp.exe"),
            StringStruct("ProductName", "Focus"),
            StringStruct("ProductVersion", __version__),
        ])]),
        VarFileInfo([VarStruct("Translation", [0x0409, 1200])]),
    ],
)

a = Analysis(
    ["run.py"],
    pathex=[],
    binaries=[],
    # Only what the app loads at run time — not the icon-building scripts.
    datas=[
        ("app/assets/fonts", "app/assets/fonts"),
        ("app/assets/icons", "app/assets/icons"),
        ("app/assets/icon.ico", "app/assets"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FocusApp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX-packed executables are a common antivirus false positive.
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=os.path.join("app", "assets", "icon.ico"),
    version=version_info,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="FocusApp",
)
