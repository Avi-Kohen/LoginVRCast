import os, re, subprocess

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_DIR  = os.path.join(APP_ROOT, "bin")

ADB = os.path.join(BIN_DIR, "adb.exe")
SCRCPY = os.path.join(BIN_DIR, "scrcpy.exe")

def _run(cmd):
    return subprocess.run(cmd, cwd=BIN_DIR, text=True, capture_output=True, encoding="utf-8", errors="ignore")

def adb_devices():
    if not os.path.exists(ADB):
        return []
    out = _run([ADB, "devices"])
    if out.returncode != 0:
        return []
    lines = [l.strip() for l in out.stdout.splitlines()[1:] if l.strip()]
    return [l.split()[0] for l in lines if "device" in l]

def first_device_or_none():
    """עדיפות ל-Wi-Fi (IP:PORT), אחרת USB"""
    devs = adb_devices()
    if not devs:
        return None
    # קודם חפש IP:PORT
    for d in devs:
        if _is_ip_serial(d):
            return d
    # אחרת חזור על הראשון (USB)
    return devs[0]

def _is_ip_serial(serial: str) -> bool:
    import re
    return ":" in serial and re.match(r"^\d{1,3}(\.\d{1,3}){3}:\d{2,5}$", serial) is not None

def first_usb_device_or_none():
    """USB בלבד"""
    devs = adb_devices()
    for d in devs:
        if not _is_ip_serial(d):
            return d
    return None

def status():
    dev = first_device_or_none()
    return {"state": "ready", "text": f"מכשיר מזוהה: {dev}"} if dev else {"state": "none", "text": "אין מכשיר מחובר"}

def wireless_connect(ip_port: str, pairing_code: str = None):
    # kept for manual mode (not used in auto flow)
    if pairing_code:
        subprocess.call([ADB, "pair", ip_port, pairing_code])
    return subprocess.call([ADB, "connect", ip_port])

def _get_ip_from_iface(serial: str, iface: str) -> str | None:
    # 2a) ip -o -4 addr show iface
    out = _run([ADB, "-s", serial, "shell", "ip", "-o", "-4", "addr", "show", iface])
    if out.returncode == 0:
        m = re.search(r"\binet\s+(\d{1,3}(?:\.\d{1,3}){3})/", out.stdout)
        if m:
            return m.group(1)

    # 3) getprop dhcp.<iface>.ipaddress
    out = _run([ADB, "-s", serial, "shell", "getprop", f"dhcp.{iface}.ipaddress"])
    if out.returncode == 0:
        val = (out.stdout or "").strip()
        if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", val):
            return val

    # 4) ifconfig iface
    out = _run([ADB, "-s", serial, "shell", "ifconfig", iface])
    if out.returncode == 0:
        # תבניות אפשריות: 'inet addr:X.X.X.X' או 'inet X.X.X.X'
        m = re.search(r"\binet(?:\s+addr:|\s+)(\d{1,3}(?:\.\d{1,3}){3})", out.stdout)
        if m:
            return m.group(1)
    return None

def _get_wifi_ip(serial: str) -> str | None:
    """
    שליפת IP אלחוטי בצורה עמידה:
    1) ip route get 8.8.8.8 -> 'dev <IFACE> src X.X.X.X'
    2) ip -o -4 addr show <IFACE> -> ... 'inet X.X.X.X/..'
    3) getprop dhcp.<IFACE>.ipaddress
    4) ifconfig <IFACE> -> 'inet addr:X.X.X.X' או 'inet X.X.X.X'
    אם לא נמצא iface, ננסה ברירת מחדל 'wlan0'/'wlan1'.
    """
    # 1) נסה למצוא גם iface וגם src
    out = _run([ADB, "-s", serial, "shell", "ip", "route", "get", "8.8.8.8"])
    if out.returncode == 0:
        # דוגמה: '... dev wlan0 src 192.168.1.50 ...'
        m = re.search(r"\bdev\s+(\S+)", out.stdout)
        iface = m.group(1) if m else None
        m = re.search(r"\bsrc\s+(\d{1,3}(?:\.\d{1,3}){3})", out.stdout)
        if m:
            return m.group(1)
        # יש iface אבל אין src? ננסה שלב 2 עם iface שמצאנו
        if iface:
            ip = _get_ip_from_iface(serial, iface)
            if ip:
                return ip

    # 2) אם לא מצאנו iface קודם, ננסה לבדוק מה יש ברשימת נתיבים כללית
    out = _run([ADB, "-s", serial, "shell", "ip", "route"])
    iface = None
    if out.returncode == 0:
        # נחפש 'wlanX' בשורות 'default via ... dev wlan0'
        m = re.search(r"\bdev\s+(wlan\d*)", out.stdout)
        if m:
            iface = m.group(1)

    # אם עדיין אין iface, ננסה ניחוש נפוץ
    for candidate in [iface, "wlan0", "wlan1"]:
        if not candidate:
            continue
        ip = _get_ip_from_iface(serial, candidate)
        if ip:
            return ip

    return None

def wireless_auto():
    """
    One-click wireless עם דיבוג טוב:
      - USB בלבד (אם כבר IP מחובר, נחזיר הצלחה)
      - adb tcpip 5555
      - שליפת כתובת IP יציבה (ראה למעלה)
      - adb connect <ip>:5555
    """
    usb = first_usb_device_or_none()
    if not usb:
        ip_dev = first_device_or_none()
        if ip_dev and _is_ip_serial(ip_dev):
            return True, f"המכשיר כבר מחובר אלחוטית ({ip_dev}). אפשר לנתק את הכבל."
        return False, "לא נמצא מכשיר USB. ודא שה‑Quest מחובר וש־ADB מזהה אותו (Developer Mode + אישור Debug)."

    # מעבר ל‑tcpip 5555
    out = _run([ADB, "-s", usb, "tcpip", "5555"])
    if out.returncode != 0:
        return False, f"שגיאה במעבר למצב אלחוטי (tcpip 5555):\nSTDOUT:\n{out.stdout}\nSTDERR:\n{out.stderr}"

    # שליפת IP אמינה
    ip = _get_wifi_ip(usb)
    if not ip:
        # נציג פלט דיאגנוסטיקה שיעזור
        diag_route = _run([ADB, "-s", usb, "shell", "ip", "route"])
        diag_addr  = _run([ADB, "-s", usb, "shell", "ip", "-o", "-4", "addr"])
        diag_prop  = _run([ADB, "-s", usb, "shell", "getprop"])
        return False, (
            "לא הצלחתי לאתר את כתובת ה‑IP של המכשיר.\n"
            "בדוק ש‑Wi‑Fi פעיל ושאתה מחובר לאותה רשת.\n\n"
            f"ip route:\n{diag_route.stdout}\n"
            f"ip -o -4 addr:\n{diag_addr.stdout}\n"
            # getprop ארוך—אם תרצה נציג רק אם צריך:
            # f"getprop (קיצור):\n{diag_prop.stdout[:800]}\n"
        )

    target = f"{ip}:5555"
    out = _run([ADB, "connect", target])
    text = (out.stdout + out.stderr).lower()
    if out.returncode != 0 or ("connected to" not in text and "already connected" not in text):
        return False, f"חיבור אלחוטי נכשל אל {target}:\nSTDOUT:\n{out.stdout}\nSTDERR:\n{out.stderr}"

    return True, f"החיבור האלחוטי הצליח אל {target}. אפשר לנתק את הכבל."

def _map_renderer_name(human_name: str) -> str:
    name = (human_name or "").strip().lower()
    if name.startswith("open"):
        return "opengl"
    return "direct3d"

def start_scrcpy(renderer: str = "OpenGL"):
    sdl_driver = _map_renderer_name(renderer)

    args = [
        SCRCPY,
        "--no-audio",
        "--crop=1600:904:2017:510",
        "--always-on-top",
        f"--render-driver={sdl_driver}",  # CLI hint to SDL
    ]

    dev = first_device_or_none()
    if dev:
        args.append(f"--serial={dev}")

    # Pass a fresh environment so renderer changes take effect every run
    env = os.environ.copy()
    env["SDL_RENDER_DRIVER"] = sdl_driver

    return subprocess.Popen(args, cwd=BIN_DIR, env=env)
