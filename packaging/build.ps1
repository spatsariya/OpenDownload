$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
function Check-Result {
    if ($LASTEXITCODE -ne 0) { throw "Build command failed: $LASTEXITCODE" }
}
python -m pip install --user pyinstaller==6.22.3 pillow==13.0.0
Check-Result
python packaging\make_icon.py
Check-Result
python -m PyInstaller --noconfirm --clean --windowed --onedir --name OpenDownload --icon assets\OpenDownload.ico --version-file packaging\version.txt --exclude-module PIL --exclude-module pytest --exclude-module numpy app.py
Check-Result
$pythonBase = python -c "import sys; print(sys.base_prefix)"
Copy-Item -LiteralPath (Join-Path $pythonBase 'LICENSE.txt') -Destination 'dist\OpenDownload\PYTHON-LICENSE.txt'
Copy-Item -LiteralPath 'README.md' -Destination 'dist\OpenDownload\README.md'
if (!(Test-Path '.build-tools-wix4\wix.exe')) {
    dotnet tool install --tool-path .build-tools-wix4 wix --version 4.0.6
    Check-Result
}
$env:DOTNET_ROLL_FORWARD = 'Major'
.\.build-tools-wix4\wix.exe extension add WixToolset.UI.wixext/4.0.6
Check-Result
python packaging\make_msi.py
Check-Result
.\.build-tools-wix4\wix.exe build packaging\OpenDownload.wxs -arch x64 -ext WixToolset.UI.wixext -o release\OpenDownload-0.1.0-x64.msi
Check-Result
Get-FileHash 'release\OpenDownload-0.1.0-x64.msi' -Algorithm SHA256
