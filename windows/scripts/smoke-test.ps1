param([string]$Version='3.1.0')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$source=Split-Path -Parent $PSScriptRoot
$setup=Join-Path $source "dist\EG-Clicker-Windows-Setup-$Version.exe"
$installed=Join-Path $env:RUNNER_TEMP 'EG native installer smoke'
$report=Join-Path $env:RUNNER_TEMP 'eg-installed-self-test.json'
$install=Start-Process -FilePath $setup -ArgumentList "/S /D=$installed" -Wait -PassThru
if($install.ExitCode -ne 0){throw "Installer failed: $($install.ExitCode)"}
$app=Join-Path $installed 'EG-Clicker.exe'
if(-not(Test-Path -LiteralPath $app)){throw 'Installed executable is missing.'}
$process=Start-Process -FilePath $app -ArgumentList "--self-test --output `"$report`"" -Wait -PassThru
if(Test-Path -LiteralPath $report){Get-Content -LiteralPath $report}
if($process.ExitCode -ne 0){throw "Installed runtime self-test failed: $($process.ExitCode)"}
$data=Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
if(-not $data.frozen -or $data.runtime -ne 'ok' -or $data.input_sent){throw 'Installed runtime report is invalid.'}
$uninstaller=Join-Path $installed 'Uninstall.exe'
$remove=Start-Process -FilePath $uninstaller -ArgumentList '/S' -Wait -PassThru
if($remove.ExitCode -ne 0){throw "Uninstaller failed: $($remove.ExitCode)"}
for($i=0; $i -lt 50 -and (Test-Path -LiteralPath $app); $i++){Start-Sleep -Milliseconds 200}
if(Test-Path -LiteralPath $app){throw 'Uninstaller left the application executable behind.'}
Write-Host 'Per-user install, frozen runtime/Tk/Win32 ABI, and uninstall verified without sending input.'
