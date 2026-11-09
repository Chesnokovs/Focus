@echo off
echo === Building Focus App (PySide6) ===
echo.

REM Make sure dependencies are present.
pip install pyinstaller PySide6 Pillow

echo.
echo === Creating executable ===
echo.

REM --add-data "src;dst" bundles fonts, icons, etc. so the running .exe
REM can resolve them via Path(__file__).parent / "assets" / ...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "FocusApp" ^
    --clean ^
    --icon "app/assets/icon.ico" ^
    --add-data "app/assets;app/assets" ^
    run.py

echo.
echo === Done! ===
echo Executable: dist\FocusApp.exe
echo.
echo Data files (focus_tasks.json, focus_images\) live next to the .exe.
pause
