#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#ifndef ROOT
  #define ROOT ".."
#endif
#ifndef RELEASE
  #define RELEASE "..\releases"
#endif

[Setup]
AppId={{3D5B3AF8-8A35-45D1-9A05-1D4D4E0A1201}}
AppName=HR-OTO Owner
AppVersion={#AppVersion}
DefaultDirName={autopf}\HR-OTO\Owner
DefaultGroupName=HR-OTO
OutputDir={#RELEASE}
OutputBaseFilename=HR-OTO-Owner-Setup
UninstallDisplayIcon={app}\hr_oto_owner.exe
SetupIconFile={#ROOT}\assets\branding\oto-hr-logo.ico
PrivilegesRequired=admin

[Files]
Source: "{#ROOT}\apps\owner_flutter\build\windows\x64\runner\Release\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autodesktop}\HR-OTO Owner"; Filename: "{app}\hr_oto_owner.exe"
Name: "{group}\HR-OTO Owner"; Filename: "{app}\hr_oto_owner.exe"

[Run]
Filename: "{app}\hr_oto_owner.exe"; Description: "Launch HR-OTO Owner"; Flags: nowait postinstall skipifsilent

