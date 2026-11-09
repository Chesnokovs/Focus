@echo off
REM Builds the Focus App installer: dist\FocusApp-Setup-<version>.exe
REM
REM   build.bat             build, then wait for a key press
REM   build.bat --no-pause  build and exit (for scripts)
REM
REM Needs: Python 3.10+ and Inno Setup 6 (https://jrsoftware.org/isdl.php).
REM Python packages are installed into a private .venv, not system-wide.

setlocal
cd /d "%~dp0"

echo === Focus App build ===
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Creating build environment in .venv ...
    py -3 -m venv .venv 2>nul || python -m venv .venv || goto :fail
)
set "PY=.venv\Scripts\python.exe"

echo Installing build dependencies ...
%PY% -m pip install --quiet --disable-pip-version-check -r requirements.txt || goto :fail

echo.
echo === 1/2 Application (PyInstaller) ===
%PY% -m PyInstaller FocusApp.spec --noconfirm --clean --distpath build\app --workpath build\work || goto :fail

echo.
echo === 2/2 Installer (Inno Setup) ===
set "ISCC="
for %%p in (
    "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
    "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
    "%ProgramFiles%\Inno Setup 6\ISCC.exe"
) do if exist %%p set "ISCC=%%~p"
if not defined ISCC for %%i in (ISCC.exe) do set "ISCC=%%~$PATH:i"
if not defined ISCC (
    echo Inno Setup 6 was not found. Install it from https://jrsoftware.org/isdl.php
    goto :fail
)
"%ISCC%" /Qp installer\FocusApp.iss || goto :fail

echo.
echo === Done ===
echo Installer:  dist\FocusApp-Setup-*.exe
echo Unpacked:   build\app\FocusApp\FocusApp.exe
echo User data lives in %%APPDATA%%\FocusApp and is not part of the build.
set "RESULT=0"
goto :end

:fail
echo.
echo *** Build failed ***
set "RESULT=1"

:end
if /i not "%~1"=="--no-pause" pause
exit /b %RESULT%
