; Inno Setup script for Focus App. Compiled by build.bat after PyInstaller
; has produced build\app\FocusApp\.
;
; Goals:
;   - works on any 64-bit Windows 10 / 11 PC with nothing preinstalled
;     (Python, Qt and the MSVC runtime are all inside the app folder);
;   - installs for the current user without administrator rights;
;   - upgrades in place and never touches the user's data, which lives in
;     %APPDATA%\FocusApp, outside the install folder.

#define AppName "Focus"
#define AppExeName "FocusApp.exe"
#define BuiltDir "..\build\app\FocusApp"
; The version is stamped into the .exe by FocusApp.spec (from app/__init__.py).
#define AppVersion GetStringFileInfo(BuiltDir + "\" + AppExeName, "ProductVersion")

[Setup]
; Identifies the app across versions. Never change it, or upgrades will
; install side by side instead of replacing the previous version.
AppId={{6C0E3E0B-8E4B-4B5F-9C1D-2F3A7B9D5E41}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Chesnokovs
AppPublisherURL=https://github.com/Chesnokovs/Focus
AppSupportURL=https://github.com/Chesnokovs/Focus/issues
VersionInfoVersion={#AppVersion}

; Per-user install by default (no UAC prompt). The user may pick
; "for all users" in the dialog if they have administrator rights.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={autopf}\{#AppName}
DisableProgramGroupPage=yes
DisableDirPage=auto

; The bundled Qt 6 needs 64-bit Windows 10 (1809) or later. On anything
; older Setup stops with a clear message instead of installing a broken app.
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763

; Focus keeps running in the tray after its window is closed. The app holds
; this mutex (see app/main.py), so Setup and Uninstall can ask the user to
; quit it before files are replaced.
AppMutex=FocusAppRunningMutex
CloseApplications=no

OutputDir=..\dist
OutputBaseFilename=FocusApp-Setup-{#AppVersion}
SetupIconFile=..\app\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Start {#AppName} when I sign in to Windows (hidden in the tray)"; GroupDescription: "{cm:AutoStartProgramGroupDescription}"; Flags: unchecked

[InstallDelete]
; On upgrade, drop the previous version's libraries so files that no longer
; exist in the new build are not left behind.
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "{#BuiltDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
; Autostart: launch straight into the tray. Removed on uninstall, and on a
; reinstall where the task is unticked.
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "FocusApp"; ValueData: """{app}\{#AppExeName}"" --minimized"; Flags: uninsdeletevalue; Tasks: autostart
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "FocusApp"; Flags: deletevalue; Tasks: not autostart

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
