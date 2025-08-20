import os, re, subprocess, time

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_DIR  = os.path.join(APP_ROOT, "bin")

ADB = os.path.join(BIN_DIR, "adb.exe")
SCRCPY = os.path.join(BIN_DIR, "scrcpy.exe")

CREATE_NO_WINDOW = 0x08000000
ADB_TIMEOUT_SEC  = 4
WIRELESS_PORT    = "5555"

def _run(cmd):
    return subprocess.run(
        cmd, cwd=BIN_DIR, text=True, capture_output=True, encoding="utf-8",
        errors="ignore", timeout=ADB_TIMEOUT_SEC, creationflags=CREATE_NO_WINDOW
    )

# ---------- helpers from the working app ----------

def _devices_output() -> str:
    return _run([ADB, "devices", "-l"]).stdout if os.path.exists(ADB) else ""

def _is_ip_serial(serial: str) -> bool:
    return ":" in serial and re.match(r"^\d{1,3}(\.\d{1,3}){3}:\d{2,5}$", serial) is not None

def quest_state():
    """
    מחזיר (transport, state, serial) עם עדיפות ל‑Wi‑Fi.
    transport ∈ {"wifi","usb",None}, state ∈ {"device","unauthorized","offline",""}
    """
    wifi_row = None
    usb_row  = None
    out = _devices_output().splitlines()
    for line in out[1:]:
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, state = parts[0], parts[1]
        if _is_ip_serial(serial):
            if wifi_row is None:
                wifi_row = ("wifi", state, serial)
        else:
            if usb_row is None:
                usb_row = ("usb", state, serial)
    return wifi_row or usb_row or (None, "", None)

def adb_devices():
    # רק רשימת serial-ים במצב device (נוח לשימוש פנימי)
    out = _devices_output().splitlines()
    res = []
    for line in out[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            res.append(parts[0])
    return res

def first_device_or_none():
    # עדיפות ל‑Wi‑Fi, אחרת USB
    transport, state, serial = quest_state()
    return serial if serial else None

def first_usb_device_or_none():
    for line in _devices_output().splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] in ("device", "unauthorized", "offline"):
            serial = parts[0]
            if not _is_ip_serial(serial):
                return serial
    return None

def status():
    """
    מצב קריא ל-UI על בסיס quest_state():
    - state: "ready" | "pairing" | "none" | "casting" (ה-"casting" ייקבע ב-main.py אם תהליך חי)
    - text: טקסט ידידותי להצגה למשתמש
    """
    transport, state, serial = quest_state()

    # אין שום התקן נראה
    if not serial:
        return {"state": "none", "text": "אין מכשיר מחובר"}

    # התקן מזוהה אבל לא מוכן (צריך לאשר Debug)
    if state == "unauthorized":
        side = "אלחוטית" if (transport == "wifi") else "בכבל"
        return {"state": "pairing", "text": f"מכשיר {side} מזוהה אך לא אושר ADB. אשר 'Always allow' ב-Quest."}

    # התקן אוף-ליין / לא יציב
    if state == "offline":
        side = "אלחוטית" if (transport == "wifi") else "בכבל"
        return {"state": "none", "text": f"מכשיר {side} במצב offline. נתק וחבר שוב / חבר USB מחדש."}

    # התקן מוכן ("device")
    if state == "device":
        if transport == "wifi":
            return {"state": "ready", "text": f"מכשיר מחובר אלחוטית: {serial}"}
        else:
            return {"state": "ready", "text": f"מכשיר מחובר בכבל: {serial}"}

    # ברירת מחדל זהירה
    return {"state": "none", "text": "לא ניתן לקבוע מצב חיבור. נסה לחבר מחדש."}

def _wifi_ip(serial: str) -> str | None:
    """
    IP דרך ממשק wlan0 (כמו באפליקציה שעובדת אצלך).
    """
    out = _run([ADB, "-s", serial, "shell", "ip", "-f", "inet", "addr", "show", "wlan0"]).stdout
    m = re.search(r"\binet\s+(\d{1,3}(?:\.\d{1,3}){3})", out)
    return m.group(1) if m else None

# ---------- one-click wireless ----------

def wireless_auto():
    """
    זרימה אוטומטית:
    1) אם כבר יש Wi‑Fi ב-`adb devices` → הצלחה מיד.
    2) אחרת חפש USB במצב 'device' (או המתן קצת לאישור).
    3) adb -s <usb> tcpip 5555
    4) שלוף IP מ-wlan0
    5) adb connect <ip>:5555
    """
    # 1) כבר מחובר אלחוטית?
    t, s, ser = quest_state()
    if t == "wifi" and s == "device":
        return True, f"המכשיר כבר מחובר אלחוטית ({ser}). אפשר לנתק את הכבל."

    # 2) המתן עד 6 שניות לאישור USB (3 ניסיונות)
    usb = None
    for _ in range(3):
        tt, st, sr = quest_state()
        if tt == "usb" and st == "device":
            usb = sr
            break
        time.sleep(2)
    if not usb:
        return False, "לא נמצא USB במצב 'device'. ודא שחיברת כבל ואישרת Debug (Always allow)."

    # 3) מעבר ל-tcpip
    out = _run([ADB, "-s", usb, "tcpip", WIRELESS_PORT])
    if out.returncode != 0:
        return False, f"שגיאה במעבר ל-tcpip {WIRELESS_PORT}:\n{out.stdout}\n{out.stderr}"

    # 4) שליפת IP
    ip = _wifi_ip(usb)
    if not ip:
        # נסה פעם נוספת אחרי רגע קטן (לפעמים ה‑wlan0 מתעדכן)
        time.sleep(1.0)
        ip = _wifi_ip(usb)
    if not ip:
        return False, "לא נמצא IP ב-wlan0. ודא שה‑Wi‑Fi פעיל באותו ה‑LAN."

    # 5) חיבור
    target = f"{ip}:{WIRELESS_PORT}"
    out = _run([ADB, "connect", target])
    txt = (out.stdout + out.stderr).lower()
    if out.returncode != 0 or ("connected to" not in txt and "already connected" not in txt):
        return False, f"חיבור אל {target} נכשל:\n{out.stdout}\n{out.stderr}"

    return True, f"החיבור האלחוטי הצליח אל {target}. אפשר לנתק את הכבל."

# ---------- renderer + launch (ללא שינויי רינדור שלך) ----------

def _map_renderer_name(human_name: str) -> str:
    name = (human_name or "").strip().lower()
    return "opengl" if name.startswith("open") else "direct3d"

def start_scrcpy(renderer: str = "OpenGL"):
    sdl_driver = _map_renderer_name(renderer)
    args = [
        SCRCPY,
        "--no-audio",
        "--crop=1600:904:2017:510",
        "--always-on-top",
        f"--render-driver={sdl_driver}",
    ]
    dev = first_device_or_none()
    if dev:
        args.append(f"--serial={dev}")

    env = os.environ.copy()
    env["SDL_RENDER_DRIVER"] = sdl_driver
    return subprocess.Popen(args, cwd=BIN_DIR, env=env, creationflags=CREATE_NO_WINDOW)
