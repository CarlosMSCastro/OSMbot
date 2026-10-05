; Inno Setup script for the OSMbot installer (D-016). Built by: python tools/build_portable.py --installer
; Installs per user (no administrator needed) into %LOCALAPPDATA%\OSMbot. The login session lives in
; %USERPROFILE%\.osmbot and is NOT touched by installing or uninstalling.
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef SourceDir
  #error SourceDir is required
#endif
#ifndef OutDir
  #define OutDir "."
#endif

[Setup]
AppId={{7DC50A31-D259-4600-AC14-85D3949F917F}
AppName=OSMbot
AppVersion={#AppVersion}
AppPublisher=OSMbot
DefaultDirName={localappdata}\OSMbot
DefaultGroupName=OSMbot
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutDir}
OutputBaseFilename=OSMbot-Setup
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\osmbot.ico
#ifdef IconFile
SetupIconFile={#IconFile}
#endif

[Languages]
Name: "pt"; MessagesFile: "compiler:Languages\Portuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho no ambiente de trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\OSMbot"; Filename: "{app}\OSMbot.exe"; WorkingDir: "{app}"; IconFilename: "{app}\osmbot.ico"
Name: "{autodesktop}\OSMbot"; Filename: "{app}\OSMbot.exe"; WorkingDir: "{app}"; IconFilename: "{app}\osmbot.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\OSMbot.exe"; Description: "Abrir o OSMbot agora"; WorkingDir: "{app}"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\app\osmbot\__pycache__"
