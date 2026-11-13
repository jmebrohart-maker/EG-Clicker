Unicode true
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"
!ifndef AppVersion
  !define AppVersion "3.1.0"
!endif
!ifndef BuildRoot
  !define BuildRoot "..\dist"
!endif
!ifndef SourceRoot
  !define SourceRoot ".."
!endif
Name "EG-Clicker for Windows ${AppVersion}"
OutFile "${BuildRoot}\EG-Clicker-Windows-Setup-${AppVersion}.exe"
InstallDir "$LOCALAPPDATA\Programs\Ehrhart Group\EG-Clicker"
InstallDirRegKey HKCU "Software\Ehrhart Group\EG-Clicker" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
AutoCloseWindow true
BrandingText "Ehrhart Group LLC"
!define MUI_ICON "${SourceRoot}\assets\eg-clicker.ico"
!define MUI_UNICON "${SourceRoot}\assets\eg-clicker.ico"
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"
VIProductVersion "${AppVersion}.0"
VIAddVersionKey /LANG=1033 "ProductName" "EG-Clicker for Windows"
VIAddVersionKey /LANG=1033 "CompanyName" "Ehrhart Group LLC"
VIAddVersionKey /LANG=1033 "FileDescription" "EG-Clicker Windows Setup"
VIAddVersionKey /LANG=1033 "FileVersion" "${AppVersion}.0"
VIAddVersionKey /LANG=1033 "ProductVersion" "${AppVersion}"
VIAddVersionKey /LANG=1033 "LegalCopyright" "Copyright (c) 2026 jmebrohart-maker. MIT License."

!macro CheckInstance
  System::Call 'kernel32::CreateMutexW(p 0, i 0, w "Local\EhrhartGroup.EGClicker.Windows") p.r0 ?e'
  Pop $1
  System::Call 'kernel32::CloseHandle(p r0)'
  ${If} $1 == 183
    MessageBox MB_OK|MB_ICONEXCLAMATION "Close EG-Clicker before continuing."
    Abort
  ${EndIf}
!macroend

Function .onInit
  SetShellVarContext current
  ${IfNot} ${RunningX64}
    MessageBox MB_OK|MB_ICONSTOP "This package requires Windows 11 x64."
    Abort
  ${EndIf}
  SetRegView 64
  ReadRegStr $0 HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion" "CurrentBuildNumber"
  ${If} $0 < 22000
    MessageBox MB_OK|MB_ICONSTOP "This package requires Windows 11 or newer."
    Abort
  ${EndIf}
  !insertmacro CheckInstance
FunctionEnd

Function un.onInit
  SetShellVarContext current
  SetRegView 64
  !insertmacro CheckInstance
FunctionEnd

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "${BuildRoot}\app\EG-Clicker\*"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Ehrhart Group\EG-Clicker" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\EhrhartGroup.EGClicker" "DisplayName" "EG-Clicker for Windows"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\EhrhartGroup.EGClicker" "DisplayVersion" "${AppVersion}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\EhrhartGroup.EGClicker" "Publisher" "Ehrhart Group LLC"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\EhrhartGroup.EGClicker" "DisplayIcon" '$"$INSTDIR\EG-Clicker.exe$"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\EhrhartGroup.EGClicker" "UninstallString" '$"$INSTDIR\Uninstall.exe$"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\EhrhartGroup.EGClicker" "QuietUninstallString" '$"$INSTDIR\Uninstall.exe$" /S'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\EhrhartGroup.EGClicker" "URLInfoAbout" "https://ehrhartgroup.us"
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\EhrhartGroup.EGClicker" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\EhrhartGroup.EGClicker" "NoRepair" 1
  Delete "$SMPROGRAMS\EG-Clicker.lnk"
  Delete "$SMPROGRAMS\Uninstall EG-Clicker.lnk"
  CreateDirectory "$SMPROGRAMS\Ehrhart Group\EG-Clicker"
  CreateShortCut "$SMPROGRAMS\Ehrhart Group\EG-Clicker\EG-Clicker.lnk" "$INSTDIR\EG-Clicker.exe"
  CreateShortCut "$SMPROGRAMS\Ehrhart Group\EG-Clicker\Uninstall EG-Clicker.lnk" "$INSTDIR\Uninstall.exe"
  CreateShortCut "$DESKTOP\EG-Clicker.lnk" "$INSTDIR\EG-Clicker.exe"
  IfSilent +2
    Exec '$"$INSTDIR\EG-Clicker.exe$"'
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\EG-Clicker.lnk"
  Delete "$SMPROGRAMS\Ehrhart Group\EG-Clicker\EG-Clicker.lnk"
  Delete "$SMPROGRAMS\Ehrhart Group\EG-Clicker\Uninstall EG-Clicker.lnk"
  RMDir "$SMPROGRAMS\Ehrhart Group\EG-Clicker"
  RMDir "$SMPROGRAMS\Ehrhart Group"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\EhrhartGroup.EGClicker"
  DeleteRegKey HKCU "Software\Ehrhart Group\EG-Clicker"
  Delete "$INSTDIR\EG-Clicker.exe"
  Delete "$INSTDIR\LICENSE.txt"
  RMDir /r "$INSTDIR\THIRD-PARTY-LICENSES"
  RMDir /r "$INSTDIR\_internal"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
SectionEnd
