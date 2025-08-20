# Build script for LoginVRCast (simplified, quote-safe)
# Usage: powershell -ExecutionPolicy Bypass -File build.ps1

$ErrorActionPreference = "Stop"

# Activate venv if present
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    . .\.venv\Scripts\Activate.ps1
}

# Install deps
pip install --upgrade pip
pip install -r requirements.txt pyinstaller

# Build one-file EXE using spec
pyinstaller --clean --noconfirm LoginVRCast.spec

# Build portable one-dir (friendlier to some AV)
pyinstaller --noconfirm --onedir --name LoginVRCast_portable app\main.py --add-binary "bin\adb.exe;bin" --add-binary "bin\AdbWinApi.dll;bin" --add-binary "bin\AdbWinUsbApi.dll;bin" --add-binary "bin\scrcpy.exe;bin" --add-binary "bin\scrcpy-server;bin" --version-file "file_version_info.txt" --icon "icon.ico"

# Zip portable folder
if (Test-Path ".\dist\LoginVRCast_portable") {
    if (Test-Path ".\dist\LoginVRCast_portable.zip") {
        Remove-Item ".\dist\LoginVRCast_portable.zip" -Force
    }

    # המתן שניה כדי לוודא ש-PyInstaller שחרר קבצים
    Start-Sleep -Seconds 2

    # דחוס את כל התוכן של התיקייה, לא את התיקייה עצמה
    Compress-Archive -Path ".\dist\LoginVRCast_portable\*" `
                     -DestinationPath ".\dist\LoginVRCast_portable.zip" `
                     -Force
}


# Checksums (use Get-FileHash to avoid certutil)
if (Test-Path ".\dist\LoginVRCast.exe") {
    (Get-FileHash ".\dist\LoginVRCast.exe" -Algorithm SHA256).Hash | Out-File ".\dist\LoginVRCast.exe.sha256.txt" -Encoding ascii
}
if (Test-Path ".\dist\LoginVRCast_portable.zip") {
    (Get-FileHash ".\dist\LoginVRCast_portable.zip" -Algorithm SHA256).Hash | Out-File ".\dist\LoginVRCast_portable.zip.sha256.txt" -Encoding ascii
}

Write-Host "Build complete. Artifacts are in the dist folder."
