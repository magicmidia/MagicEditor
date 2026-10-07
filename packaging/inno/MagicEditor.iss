; MagicEditor — Inno Setup 6 installer
; Build: scripts/build.ps1 -Inno  (requires ISCC on PATH or ISCC_PATH)
;
; Features:
;   - Program Files install + Start Menu / Desktop shortcuts
;   - ProgID MagicEditor.Document + OpenWithProgids for text extensions
;   - Optional set-as-default associations
;   - Context menu *\shell  "Editar com MagicEditor"
;   - Default Programs capabilities
;   - Installer wizard: default UI language + theme → HKCU QSettings

#define MyAppName "MagicEditor"
#ifndef MyAppVersion
  #define MyAppVersion "0.9.9"
#endif
#define MyAppPublisher "MagicEditor Contributors"
#define MyAppURL "https://github.com/magicmidia/MagicEditor"
#define MyAppExeName "MagicEditor.exe"
; Same product line as WiX UpgradeCode family
#define MyAppId "{{A7C3E9F1-4B2D-4E8A-9C1F-6D5E8B0A2F34}"

#ifndef SourceExe
  #define SourceExe "..\..\dist\MagicEditor.exe"
#endif
#ifndef SourceIcon
  #define SourceIcon "..\..\resources\icons\app\magiceditor.ico"
#endif

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=
OutputDir=..\..\dist
OutputBaseFilename=MagicEditor-{#MyAppVersion}-win64-setup
SetupIconFile={#SourceIcon}
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
ChangesAssociations=yes
CloseApplications=yes
RestartApplications=no
MinVersion=10.0
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "assocdefaults"; Description: "Associar extensões de texto/código ao MagicEditor (abrir por padrão)"; GroupDescription: "Associações de arquivos:"; Flags: checkedonce
Name: "contextmenu"; Description: "Adicionar ""Editar com MagicEditor"" ao menu de contexto"; GroupDescription: "Integração com o Windows:"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "{#SourceExe}"; DestDir: "{app}"; DestName: "{#MyAppExeName}"; Flags: ignoreversion
; Optional README if present at build time
; Source: "..\..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

; ---------------------------------------------------------------------------
; Registry — ProgID, context menu, capabilities, OpenWith + optional defaults
; ---------------------------------------------------------------------------
[Registry]
; Application install marker
Root: HKCU; Subkey: "Software\MagicEditor\MagicEditor"; ValueType: dword; ValueName: "installed"; ValueData: "1"; Flags: uninsdeletekey

; ProgID
Root: HKCR; Subkey: "MagicEditor.Document"; ValueType: string; ValueName: ""; ValueData: "MagicEditor Document"; Flags: uninsdeletekey
Root: HKCR; Subkey: "MagicEditor.Document\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKCR; Subkey: "MagicEditor.Document\shell"; ValueType: string; ValueName: ""; ValueData: "open"
Root: HKCR; Subkey: "MagicEditor.Document\shell\open"; ValueType: string; ValueName: ""; ValueData: "Abrir"
Root: HKCR; Subkey: "MagicEditor.Document\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

; Context menu on all files
Root: HKCR; Subkey: "*\shell\EditWithMagicEditor"; ValueType: string; ValueName: ""; ValueData: "Editar com MagicEditor"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "*\shell\EditWithMagicEditor"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#MyAppExeName},0"; Tasks: contextmenu
Root: HKCR; Subkey: "*\shell\EditWithMagicEditor"; ValueType: string; ValueName: "MultiSelectModel"; ValueData: "Single"; Tasks: contextmenu
Root: HKCR; Subkey: "*\shell\EditWithMagicEditor\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: contextmenu

; Also on directories (open folder as workspace-friendly open)
Root: HKCR; Subkey: "Directory\shell\EditWithMagicEditor"; ValueType: string; ValueName: ""; ValueData: "Abrir pasta no MagicEditor"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCR; Subkey: "Directory\shell\EditWithMagicEditor"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#MyAppExeName},0"; Tasks: contextmenu
Root: HKCR; Subkey: "Directory\shell\EditWithMagicEditor\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: contextmenu

; Default Programs registration
Root: HKLM; Subkey: "SOFTWARE\RegisteredApplications"; ValueType: string; ValueName: "MagicEditor"; ValueData: "Software\MagicEditor\Capabilities"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "Software\MagicEditor\Capabilities"; ValueType: string; ValueName: "ApplicationName"; ValueData: "MagicEditor"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\MagicEditor\Capabilities"; ValueType: string; ValueName: "ApplicationDescription"; ValueData: "Editor de texto e código de alto desempenho"
Root: HKLM; Subkey: "Software\MagicEditor\Capabilities\FileAssociations"; Flags: uninsdeletekeyifempty

; Repair leftover hijack: .bat/.cmd must stay executable (never uninstall these).
Root: HKCR; Subkey: ".bat"; ValueType: string; ValueName: ""; ValueData: "batfile"
Root: HKCR; Subkey: ".cmd"; ValueType: string; ValueName: ""; ValueData: "cmdfile"
Root: HKCU; Subkey: "Software\Classes\.bat"; ValueType: string; ValueName: ""; ValueData: "batfile"
Root: HKCU; Subkey: "Software\Classes\.cmd"; ValueType: string; ValueName: ""; ValueData: "cmdfile"

; Generated OpenWithProgids + optional defaults + Capabilities FileAssociations
#include "associations.issinc"

[Code]
var
  PrefsPage: TWizardPage;
  LangLabel: TNewStaticText;
  ThemeLabel: TNewStaticText;
  LangCombo: TNewComboBox;
  ThemeCombo: TNewComboBox;
  PrefsHint: TNewStaticText;

const
  SHCNE_ASSOCCHANGED = $08000000;
  SHCNF_IDLIST = $0000;

procedure SHChangeNotify(wEventId: Longint; uFlags: UINT; dwItem1, dwItem2: Integer);
  external 'SHChangeNotify@shell32.dll stdcall';

function LangCode(Index: Integer): String;
begin
  case Index of
    0: Result := 'pt_BR';
    1: Result := 'en_US';
    2: Result := 'es_ES';
  else
    Result := 'pt_BR';
  end;
end;

function ThemeCode(Index: Integer): String;
begin
  case Index of
    0: Result := 'luminous_void';
    1: Result := 'clean_light';
    2: Result := 'midnight_dark';
    3: Result := 'darcula';
    4: Result := 'cobalt_blue';
    5: Result := 'monokai_pro';
    6: Result := 'tokyo_night';
    7: Result := 'catppuccin_mocha';
    8: Result := 'nord';
    9: Result := 'rose_pine';
    10: Result := 'gruvbox_dark';
    11: Result := 'everforest';
    12: Result := 'kanagawa';
    13: Result := 'solarized_light';
  else
    Result := 'luminous_void';
  end;
end;

procedure InitializeWizard;
begin
  PrefsPage := CreateCustomPage(
    wpSelectTasks,
    'Preferências iniciais',
    'Escolha o idioma da interface e o tema padrão do MagicEditor.'
  );

  LangLabel := TNewStaticText.Create(PrefsPage);
  LangLabel.Parent := PrefsPage.Surface;
  LangLabel.Caption := 'Idioma da interface:';
  LangLabel.Left := ScaleX(0);
  LangLabel.Top := ScaleY(8);
  LangLabel.AutoSize := True;

  LangCombo := TNewComboBox.Create(PrefsPage);
  LangCombo.Parent := PrefsPage.Surface;
  LangCombo.Left := ScaleX(0);
  LangCombo.Top := LangLabel.Top + LangLabel.Height + ScaleY(6);
  LangCombo.Width := PrefsPage.SurfaceWidth;
  LangCombo.Style := csDropDownList;
  LangCombo.Items.Add('Português (Brasil)');
  LangCombo.Items.Add('English (US)');
  LangCombo.Items.Add('Español');
  LangCombo.ItemIndex := 0;

  ThemeLabel := TNewStaticText.Create(PrefsPage);
  ThemeLabel.Parent := PrefsPage.Surface;
  ThemeLabel.Caption := 'Tema visual:';
  ThemeLabel.Left := ScaleX(0);
  ThemeLabel.Top := LangCombo.Top + LangCombo.Height + ScaleY(16);
  ThemeLabel.AutoSize := True;

  ThemeCombo := TNewComboBox.Create(PrefsPage);
  ThemeCombo.Parent := PrefsPage.Surface;
  ThemeCombo.Left := ScaleX(0);
  ThemeCombo.Top := ThemeLabel.Top + ThemeLabel.Height + ScaleY(6);
  ThemeCombo.Width := PrefsPage.SurfaceWidth;
  ThemeCombo.Style := csDropDownList;
  ThemeCombo.Items.Add('Luminous Void (escuro dourado)');
  ThemeCombo.Items.Add('Clean Light');
  ThemeCombo.Items.Add('Midnight Dark');
  ThemeCombo.Items.Add('Darcula');
  ThemeCombo.Items.Add('Cobalt Blue');
  ThemeCombo.Items.Add('Monokai Pro');
  ThemeCombo.Items.Add('Tokyo Night');
  ThemeCombo.Items.Add('Catppuccin Mocha');
  ThemeCombo.Items.Add('Nord');
  ThemeCombo.Items.Add('Rosé Pine');
  ThemeCombo.Items.Add('Gruvbox');
  ThemeCombo.Items.Add('Everforest');
  ThemeCombo.Items.Add('Kanagawa');
  ThemeCombo.Items.Add('Solarized Light');
  ThemeCombo.ItemIndex := 0;

  PrefsHint := TNewStaticText.Create(PrefsPage);
  PrefsHint.Parent := PrefsPage.Surface;
  PrefsHint.Caption :=
    'Essas opções são gravadas nas preferências do usuário (HKCU) e' + #13#10 +
    'aplicadas na primeira execução. Você pode mudar depois em Configurações.';
  PrefsHint.Left := ScaleX(0);
  PrefsHint.Top := ThemeCombo.Top + ThemeCombo.Height + ScaleY(20);
  PrefsHint.Width := PrefsPage.SurfaceWidth;
  PrefsHint.WordWrap := True;
  PrefsHint.AutoSize := False;
  PrefsHint.Height := ScaleY(48);
end;

procedure WriteUserPref(const SubKey, ValueName, ValueData: String);
begin
  { QSettings NativeFormat: Software\<Org>\<App>\<group>\<key> }
  RegWriteStringValue(HKCU, 'Software\MagicEditor\MagicEditor\' + SubKey, ValueName, ValueData);
end;

procedure WriteUserPrefDword(const SubKey, ValueName: String; ValueData: Cardinal);
begin
  RegWriteDWordValue(HKCU, 'Software\MagicEditor\MagicEditor\' + SubKey, ValueName, ValueData);
end;

procedure RestoreNativeScriptHandlers;
begin
  { Older setups set MagicEditor.Document as the .bat/.cmd default.
    Explorer still shows "choose a program" if FileExts OpenWithProgids
    lists MagicEditor.Document next to batfile — wipe those leftovers. }
  RegWriteStringValue(HKEY_CLASSES_ROOT, '.bat', '', 'batfile');
  RegWriteStringValue(HKEY_CLASSES_ROOT, '.cmd', '', 'cmdfile');
  RegWriteStringValue(HKEY_CURRENT_USER, 'Software\Classes\.bat', '', 'batfile');
  RegWriteStringValue(HKEY_CURRENT_USER, 'Software\Classes\.cmd', '', 'cmdfile');
  RegDeleteValue(HKEY_CLASSES_ROOT, '.bat\OpenWithProgids', 'MagicEditor.Document');
  RegDeleteValue(HKEY_CLASSES_ROOT, '.cmd\OpenWithProgids', 'MagicEditor.Document');
  RegDeleteValue(HKEY_CURRENT_USER, 'Software\Classes\.bat\OpenWithProgids', 'MagicEditor.Document');
  RegDeleteValue(HKEY_CURRENT_USER, 'Software\Classes\.cmd\OpenWithProgids', 'MagicEditor.Document');
  RegDeleteValue(HKEY_LOCAL_MACHINE, 'Software\MagicEditor\Capabilities\FileAssociations', '.bat');
  RegDeleteValue(HKEY_LOCAL_MACHINE, 'Software\MagicEditor\Capabilities\FileAssociations', '.cmd');
  { Per-user Explorer picker cache (not covered by HKCR defaults). }
  RegDeleteKeyIncludingSubkeys(HKEY_CURRENT_USER,
    'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.bat\UserChoice');
  RegDeleteKeyIncludingSubkeys(HKEY_CURRENT_USER,
    'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.cmd\UserChoice');
  RegDeleteKeyIncludingSubkeys(HKEY_CURRENT_USER,
    'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.bat\OpenWithProgids');
  RegDeleteKeyIncludingSubkeys(HKEY_CURRENT_USER,
    'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.cmd\OpenWithProgids');
  RegDeleteKeyIncludingSubkeys(HKEY_CURRENT_USER,
    'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.bat\OpenWithList');
  RegDeleteKeyIncludingSubkeys(HKEY_CURRENT_USER,
    'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.cmd\OpenWithList');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Lang, Theme: String;
begin
  if CurStep = ssPostInstall then
  begin
    RestoreNativeScriptHandlers;
    Lang := LangCode(LangCombo.ItemIndex);
    Theme := ThemeCode(ThemeCombo.ItemIndex);

    { Install markers (WiX-compatible) }
    RegWriteStringValue(HKCU, 'Software\MagicEditor\MagicEditor', 'install_lang', Lang);
    RegWriteStringValue(HKCU, 'Software\MagicEditor\MagicEditor', 'install_theme', Theme);

    { QSettings keys used by magiceditor.services.settings }
    WriteUserPref('ui', 'language', Lang);
    WriteUserPref('ui', 'theme', Theme);
    { Skip first-run wizard so install choices stick }
    WriteUserPrefDword('ui', 'first_run_done', 1);

    { Notify shell of association changes }
    SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, 0, 0);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    RestoreNativeScriptHandlers;
    SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, 0, 0);
  end;
end;
