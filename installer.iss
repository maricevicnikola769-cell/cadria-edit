; Instalacija za CADRIA EDIT (Next -> Next -> Install).
; Verziju šalje build fajl.

#define AppName "CADRIA EDIT"
#define ExeName "CadriaEdit.exe"

[Setup]
AppId={{6E0C7B52-3B7F-4C3E-9C1A-0CAD71AED170}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Nikola Maričević
DefaultDirName={autopf}\CadriaEdit
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=CadriaEdit-Setup
SetupIconFile=app\icon.ico
UninstallDisplayIcon={app}\{#ExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\CadriaEdit\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#ExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#ExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#ExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
