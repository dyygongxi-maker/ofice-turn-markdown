#define MyAppName "廾匸转换"
#define MyAppVersion "0.3.0"
#define MyAppPublisher "廾匸转换"
#define MyAppExeName "廾匸转换.exe"

[Setup]
AppId={{8B027705-5814-4A44-AF64-5B3C2682D2EB}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\廾匸转换
DefaultGroupName=廾匸转换
DisableProgramGroupPage=yes
OutputDir=..\release
OutputBaseFilename=廾匸转换-Setup-0.3.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=..\assets\app-icon.ico

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加快捷方式："; Flags: checkedonce

[Files]
Source: "..\assets\app-icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\廾匸转换\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\廾匸转换"; Filename: "{app}\廾匸转换.exe"; IconFilename: "{app}\app-icon.ico"
Name: "{group}\卸载廾匸转换"; Filename: "{uninstallexe}"
Name: "{autodesktop}\廾匸转换"; Filename: "{app}\廾匸转换.exe"; IconFilename: "{app}\app-icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\廾匸转换.exe"; Description: "启动廾匸转换"; Flags: nowait postinstall skipifsilent
