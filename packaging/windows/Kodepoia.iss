#ifndef AppVersion
  #error AppVersion must be supplied from the canonical Kodepoia release identity
#endif
#ifndef SourceDir
  #define SourceDir "..\..\build\windows\KodepoiaStudio.dist"
#endif

#define AppName "Kodepoia"
#define AppPublisher "LaurentCOLL1"
#define AppExeName "KodepoiaStudio.exe"

[Setup]
AppId={{A67EEAB5-46C2-4B21-A169-7E17275DE2F0}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\Kodepoia
DefaultGroupName=Kodepoia
AllowNoIcons=no
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=auto
OutputDir=..\..\dist\windows
OutputBaseFilename=KodepoiaSetup
UninstallDisplayName=Kodepoia
CloseApplications=yes
RestartApplications=no
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Kodepoia"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{userdocs}"
Name: "{autodesktop}\Kodepoia"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{userdocs}"; Tasks: desktopicon
Name: "{group}\Désinstaller Kodepoia"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Lancer Kodepoia"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
