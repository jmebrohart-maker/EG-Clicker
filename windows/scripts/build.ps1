param([string]$Version = '3.1.0')
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$source = Split-Path -Parent $PSScriptRoot
$dist = Join-Path $source 'dist'
$build = Join-Path $source '.build'
if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw 'Use a semantic version.' }
if ($env:OS -ne 'Windows_NT') { throw 'Build this project on Windows x64.' }
New-Item -ItemType Directory -Force -Path $dist, $build | Out-Null
python -m PyInstaller --noconfirm --clean --windowed --onedir --name EG-Clicker --icon "$source\assets\eg-clicker.ico" --manifest "$source\packaging\app.manifest" --version-file "$source\packaging\version-info.txt" --paths "$source" --collect-submodules pycaw --collect-submodules comtypes --collect-submodules psutil --distpath "$dist\app" --workpath "$build\pyinstaller" --specpath "$build" "$source\main.py"
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }
Copy-Item -LiteralPath (Join-Path (Split-Path -Parent $source) 'LICENSE') -Destination "$dist\app\EG-Clicker\LICENSE.txt" -Force
python "$source\scripts\collect_licenses.py" "$dist\app\EG-Clicker"
if ($LASTEXITCODE -ne 0) { throw 'License collection failed.' }
$compiler = Join-Path ${env:ProgramFiles(x86)} 'NSIS\makensis.exe'
if (-not (Test-Path -LiteralPath $compiler)) { throw 'Install NSIS 3 before building the setup executable.' }
& $compiler "/DAppVersion=$Version" "/DBuildRoot=$dist" "/DSourceRoot=$source" "$source\installer\EG-Clicker.nsi"
if ($LASTEXITCODE -ne 0) { throw 'NSIS compilation failed.' }
$portable = Join-Path $dist "EG-Clicker-Windows-Portable-$Version.zip"
Compress-Archive -Path "$dist\app\EG-Clicker" -DestinationPath $portable -Force
$files = @((Join-Path $dist "EG-Clicker-Windows-Setup-$Version.exe"), $portable)
$lines = foreach ($file in $files) { '{0}  {1}' -f (Get-FileHash -Algorithm SHA256 -LiteralPath $file).Hash.ToLowerInvariant(), (Split-Path -Leaf $file) }
[IO.File]::WriteAllText((Join-Path $dist 'SHA256SUMS-Windows.txt'), (($lines -join "`n") + "`n"), (New-Object Text.UTF8Encoding($false)))
Write-Host 'Windows setup, portable bundle and checksums are ready.'
