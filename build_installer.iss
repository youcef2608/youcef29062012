; سكريبت Inno Setup لإنشاء برنامج تثبيت احترافي لـ Nabtakir Race Timer

[Setup]
AppName=Nabtakir Race Timer
AppVersion=4.1
AppPublisher=Nabtakir
DefaultDirName={autopf}\NabtakirRaceTimer
DefaultGroupName=Nabtakir Race Timer
OutputDir=.\Installer
OutputBaseFilename=Nabtakir_RaceTimer_Setup_v4.1
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; تأكد من أن مسار الملف التنفيذي أدناه هو المسار الصحيح بعد عملية البناء باستخدام PyInstaller
Source: "dist\race_timer_app.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Nabtakir Race Timer"; Filename: "{app}\race_timer_app.exe"; IconFilename: "{app}\icon.ico"
Name: "{group}\{cm:UninstallProgram,Nabtakir Race Timer}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Nabtakir Race Timer"; Filename: "{app}\race_timer_app.exe"; Tasks: desktopicon; IconFilename: "{app}\icon.ico"

[Run]
; فتح البرنامج تلقائياً بعد انتهاء التثبيت
Filename: "{app}\race_timer_app.exe"; Description: "{cm:LaunchProgram,Nabtakir Race Timer}"; Flags: nowait postinstall skipifsilent