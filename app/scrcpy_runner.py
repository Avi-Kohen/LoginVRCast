import os, subprocess

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_DIR  = os.path.join(APP_ROOT, "bin")

ADB = os.path.join(BIN_DIR, "adb.exe")
SCRCPY = os.path.join(BIN_DIR, "scrcpy.exe")
SCRCPY_SERVER = os.path.join(BIN_DIR, "scrcpy-server")  # וידוא קיום

CROP = "1600:904:2017:510"  # חיתוך עין שמאל ב-Quest

# מיפוי פרופילים בעברית -> הגדרות
PRESETS = {
    "נמוך":  {"max_size": "1280", "max_fps": "30", "bitrate": "6M"},
    "בינוני": {"max_size": "1600", "max_fps": "45", "bitrate": "10M"},
    "גבוה":  {"max_size": "1920", "max_fps": "60", "bitrate": "16M"},
}

def _check_bin():
    for p in (ADB, SCRCPY, SCRCPY_SERVER):
        if not os.path.exists(p):
            return False, f"‏קובץ חסר: {p}"
    return True, "ok"

def adb_devices():
    if not os.path.exists(ADB):
        return []
    try:
        out = subprocess.check_output([ADB, "devices"], stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="ignore")
        lines = [l.strip() for l in out.splitlines()[1:] if l.strip()]
        serials = [l.split()[0] for l in lines if "device" in l]
        return serials
    except Exception:
        return []

def first_device_or_none():
    devices = adb_devices()
    return devices[0] if devices else None

def status():
    dev = first_device_or_none()
    if dev:
        return {"state": "ready", "text": f"מכשיר מזוהה: {dev}"}
    else:
        return {"state": "none", "text": "אין מכשיר. חבר USB או השתמש ב'חיבור אלחוטי'."}

def wireless_connect(ip_port: str, pairing_code: str = None):
    """
    ip_port לדוגמה: 192.168.1.50:5555
    אם יש pairing_code, נבצע צימוד (Android 11+).
    """
    if pairing_code:
        subprocess.call([ADB, "pair", ip_port, pairing_code])
    return subprocess.call([ADB, "connect", ip_port])  # 0 = הצלחה

def start_scrcpy(preset_name: str):
    ok, msg = _check_bin()
    if not ok:
        raise RuntimeError(msg)

    preset = PRESETS.get(preset_name, PRESETS["בינוני"])

    args = [
        SCRCPY,
        "--no-audio",
        f"--crop={CROP}",
        f"--max-size={preset['max_size']}",
        f"--max-fps={preset['max_fps']}",
        f"--bit-rate={preset['bitrate']}",
        "--window-borderless",
        "--always-on-top",
        "--stay-awake",
        "--window-title=LoginVRCast",
    ]

    dev = first_device_or_none()
    if dev:
        args.append(f"--serial={dev}")

    return subprocess.Popen(args, cwd=BIN_DIR)
