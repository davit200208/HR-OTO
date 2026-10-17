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
AppId={{E4A4B85F-2DBE-4F8D-9F39-1D4D4E0A1101}}
AppName=HR-OTO Admin
AppVersion={#AppVersion}
DefaultDirName={autopf}\HR-OTO\Admin
DefaultGroupName=HR-OTO
OutputDir={#RELEASE}
OutputBaseFilename=HR-OTO-Admin-Setup
UninstallDisplayIcon={app}\hr_oto_admin.exe
SetupIconFile={#ROOT}\assets\branding\oto-hr-logo.ico
PrivilegesRequired=admin
ChangesAssociations=no

[Files]
Source: "{#ROOT}\apps\admin_flutter\build\windows\x64\runner\Release\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autodesktop}\HR-OTO Admin"; Filename: "{app}\hr_oto_admin.exe"
Name: "{group}\HR-OTO Admin"; Filename: "{app}\hr_oto_admin.exe"

[Run]
Filename: "{app}\hr_oto_admin.exe"; Description: "Launch HR-OTO Admin"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := FileExists(ExpandConstant('{#ROOT}\apps\admin_flutter\build\windows\x64\runner\Release\hr_oto_admin.exe'));
  if not Result then MsgBox('Verified Flutter Admin Release build was not found. Build was not packaged.', mbError, MB_OK);
end;
