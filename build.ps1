# Build script for LoginVRCast (both one-file and portable)
# Usage: powershell -ExecutionPolicy Bypass -File build.ps1

$ErrorActionPreference = "Stop"

# Activate venv if present
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    . .\.venv\Scripts\Activate.ps1
}

# Deps
pip install --upgrade pip
pip install -r requirements.txt pyinstaller

# Clean
if (Test-Path ".\build") { Remove-Item ".\build" -Recurse -Force }
if (Test-Path ".\dist")  { Remove-Item ".\dist"  -Recurse -Force }

# === ONE-FILE ===
pyinstaller --noconfirm --clean --onefile `
  --name "LoginVRCast" app\main.py `
  --noconsole `
  --add-binary "bin\adb.exe;." `
  --add-binary "bin\AdbWinApi.dll;." `
  --add-binary "bin\AdbWinUsbApi.dll;." `
  --add-binary "bin\scrcpy.exe;." `
  --add-binary "bin\scrcpy-server;." `
  --version-file "file_version_info.txt" `
  --icon "icon.ico"

# === PORTABLE (ONE-DIR) ===
pyinstaller --noconfirm --onedir `
  --name "LoginVRCast_portable" app\main.py `
  --noconsole `
  --add-binary "bin\adb.exe;bin" `
  --add-binary "bin\AdbWinApi.dll;bin" `
  --add-binary "bin\AdbWinUsbApi.dll;bin" `
  --add-binary "bin\scrcpy.exe;bin" `
  --add-binary "bin\scrcpy-server;bin" `
  --version-file "file_version_info.txt" `
  --icon "icon.ico"

# Zip portable folder via staging (avoids locks on base_library.zip)
$portableDir = ".\dist\LoginVRCast_portable"
$zipPath     = ".\dist\LoginVRCast_portable.zip"
$stageDir    = Join-Path $env:TEMP "LoginVRCast_portable_stage"

if (Test-Path $portableDir) {

    # 1) Ensure we are not zipping a running folder (kill any running EXE just in case)
    Get-Process -Name "LoginVRCast_portable" -ErrorAction SilentlyContinue | Stop-Process -Force

    # 2) Small wait + retry loop to let file locks clear
    $maxTries = 5
    for ($i = 1; $i -le $maxTries; $i++) {
        try {
            # Try an exclusive read to detect lock
            $test = Join-Path $portableDir "_internal\base_library.zip"
            if (Test-Path $test) {
                $fs = [System.IO.File]::Open($test, 'Open', 'Read', 'None')
                $fs.Close()
            }
            break
        } catch {
            if ($i -eq $maxTries) { throw "Portable folder is still locked after $maxTries tries." }
            Start-Sleep -Seconds 2
        }
    }

    # 3) Clean old stage + zip
    if (Test-Path $stageDir) { Remove-Item $stageDir -Recurse -Force }
    if (Test-Path $zipPath)  { Remove-Item $zipPath  -Force }

    # 4) Copy to staging (unlocked files)
    New-Item -ItemType Directory -Force -Path $stageDir | Out-Null
    robocopy $portableDir $stageDir /MIR /NFL /NDL /NJH /NJS | Out-Null

    # 5) Zip the staged copy
    Compress-Archive -Path "$stageDir\*" -DestinationPath $zipPath -Force

    # 6) Cleanup stage
    Remove-Item $stageDir -Recurse -Force
}


Write-Host "Done. One-file: dist\LoginVRCast.exe | Portable: dist\LoginVRCast_portable.zip"
if (Test-Path ".\dist\LoginVRCast.exe") {
    (Get-FileHash ".\dist\LoginVRCast.exe" -Algorithm SHA256).Hash |
        Out-File ".\dist\LoginVRCast.exe.sha256.txt" -Encoding ascii
}
if (Test-Path ".\dist\LoginVRCast_portable.zip") {
    (Get-FileHash ".\dist\LoginVRCast_portable.zip" -Algorithm SHA256).Hash |
        Out-File ".\dist\LoginVRCast_portable.zip.sha256.txt" -Encoding ascii
}