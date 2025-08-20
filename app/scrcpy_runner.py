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

def _list_wlan_ifaces(serial: str) -> list[str]:
    """
    מאתר שמות ממשקים אלחוטיים (wlan*) ומעדיף כאלה שבמצב UP.
    """
    out = _run([ADB, "-s", serial, "shell", "ip", "-o", "link", "show"])
    if out.returncode != 0:
        return []
    ifaces_up, ifaces_down = [], []
    for line in out.stdout.splitlines():
        # דוגמה: '3: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP> ...'
        parts = line.split(":")
        if len(parts) >= 3:
            name = parts[1].strip()
            if name.startswith("wlan"):
                flags = parts[2]
                if "UP" in flags:
                    ifaces_up.append(name)
                else:
                    ifaces_down.append(name)
    return ifaces_up + ifaces_down  # קודם UP, אחר כך השאר

def _get_ip_from_iface(serial: str, iface: str) -> str | None:
    # ip -o -4 addr show dev <iface>  => 'inet X.X.X.X/..'
    out = _run([ADB, "-s", serial, "shell", "ip", "-o", "-4", "addr", "show", "dev", iface])
    if out.returncode == 0:
        m = re.search(r"\binet\s+(\d{1,3}(?:\.\d{1,3}){3})/", out.stdout)
        if m:
            return m.group(1)

    # getprop dhcp.<iface>.ipaddress
    out = _run([ADB, "-s", serial, "shell", "getprop", f"dhcp.{iface}.ipaddress"])
    if out.returncode == 0:
        val = (out.stdout or "").strip()
        if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", val):
            return val

    # ifconfig <iface> (לבניות ישנות)
    out = _run([ADB, "-s", serial, "shell", "ifconfig", iface])
    if out.returncode == 0:
        m = re.search(r"\binet(?:\s+addr:|\s+)(\d{1,3}(?:\.\d{1,3}){3})", out.stdout)
        if m:
            return m.group(1)
    return None

def _wifi_ip(serial: str) -> str | None:
    """
    זיהוי IP אלחוטי אמין:
    1) ip route get 8.8.8.8 -> 'src X.X.X.X'
    2) אם אין, סרוק כל wlan* (UP תחילה) עם ip/addr/getprop/ifconfig
    3) נפילה אחרונה: חיפוש ב-getprop על dhcp.wlan*.ipaddress
    """
    # 1) מסלול ברירת מחדל
    out = _run([ADB, "-s", serial, "shell", "ip", "route", "get", "8.8.8.8"])
    if out.returncode == 0:
        m = re.search(r"\bsrc\s+(\d{1,3}(?:\.\d{1,3}){3})", out.stdout)
        if m:
            return m.group(1)

    # 2) כל wlan*
    wlans = _list_wlan_ifaces(serial)
    if not wlans:
        wlans = ["wlan0", "wlan1"]  # נסיון "עיוור" אם הרשימה ריקה
    for iface in wlans:
        ip = _get_ip_from_iface(serial, iface)
        if ip:
            return ip

    # 3) חיפוש כללי ב-getprop
    out = _run([ADB, "-s", serial, "shell", "getprop"])
    if out.returncode == 0:
        m = re.search(r"dhcp\.(wlan\d*).*?ipaddress\]\s*:\s*\[(\d{1,3}(?:\.\d{1,3}){3})\]", out.stdout)
        if m:
            return m.group(2)
    return None

# ---------- one-click wireless ----------

def wireless_auto():
    """
    זרימה אוטומטית:
      1) אם כבר מחובר Wi‑Fi → הצלחה מיד.
      2) מצא USB 'device' (המתנה קצרה לאישור אם צריך).
      3) adb tcpip 5555
      4) חכה רגע קצר ואז שלוף IP (לא רק wlan0)
      5) adb connect <ip>:5555
    """
    # 1) כבר מחובר אלחוטית?
    t, s, ser = quest_state()
    if t == "wifi" and s == "device":
        return True, f"המכשיר כבר מחובר אלחוטית ({ser}). אפשר לנתק את הכבל."

    # 2) מצא USB 'device' (עד 6 שניות)
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

    # 4) המתנה קצרה ואז שליפת IP
    time.sleep(1.0)
    ip = _wifi_ip(usb)
    if not ip:
        time.sleep(1.0)
        ip = _wifi_ip(usb)
    if not ip:
        # דיאגנוסטיקה ממוקדת – תעזור אם עדיין נכשל
        diag_route = _run([ADB, "-s", usb, "shell", "ip", "route"])
        diag_addr  = _run([ADB, "-s", usb, "shell", "ip", "-o", "-4", "addr"])
        return False, (
            "לא נמצא IP אלחוטי. ודא שה‑Wi‑Fi פעיל ושהמחשב וה‑Quest באותה רשת.\n\n"
            f"ip route:\n{diag_route.stdout}\n"
            f"ip -o -4 addr:\n{diag_addr.stdout}\n"
        )

    # 5) חיבור
    target = f"{ip}:{WIRELESS_PORT}"
    out = _run([ADB, "connect", target])
    txt = (out.stdout + out.stderr).lower()
    if out.returncode != 0 or ("connected to" not in txt and "already connected" not in txt):
        return False, f"חיבור אל {target} נכשל:\n{out.stdout}\n{out.stderr}"

    return True, f"החיבור האלחוטי הצליח אל {target}. אפשר לנתק את הכבל."

def wireless_disconnect():
    """
    ניתוק חיבור אלחוטי (adb disconnect) וחזרה ל-USB.
    """
    dev = first_device_or_none()
    if dev and _is_ip_serial(dev):
        # אם אנחנו כרגע על Wi-Fi, ננתק
        _run([ADB, "disconnect", dev])
        # החזר ל-USB (יעזור ל-ADB לחזור למצב חיבור בכבל)
        _run([ADB, "usb"])
        return True, f"החיבור האלחוטי נותק ({dev})."
    return False, "לא נמצא חיבור אלחוטי פעיל לנתק."


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
