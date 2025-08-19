import os, subprocess

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_DIR  = os.path.join(APP_ROOT, "bin")

ADB = os.path.join(BIN_DIR, "adb.exe")
SCRCPY = os.path.join(BIN_DIR, "scrcpy.exe")

def adb_devices():
    if not os.path.exists(ADB):
        return []
    try:
        out = subprocess.check_output([ADB, "devices"], text=True, encoding="utf-8", errors="ignore")
        lines = [l.strip() for l in out.splitlines()[1:] if l.strip()]
        return [l.split()[0] for l in lines if "device" in l]
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
        return {"state": "none", "text": "אין מכשיר מחובר"}

def wireless_connect(ip_port: str, pairing_code: str = None):
    if pairing_code:
        subprocess.call([ADB, "pair", ip_port, pairing_code])
    return subprocess.call([ADB, "connect", ip_port])

def _map_renderer_name(human_name: str) -> str:
    # שמות שנתמכים ב-SDL2: "direct3d", "opengl", "opengles2", "software"
    name = (human_name or "").strip().lower()
    if name.startswith("open"):
        return "opengl"
    return "direct3d"

def start_scrcpy(renderer: str = "OpenGL"):
    sdl_driver = _map_renderer_name(renderer)
    # אופציונלי: להכריח גם דרך משתנה סביבה
    os.environ.setdefault("SDL_RENDER_DRIVER", sdl_driver)

    args = [
        SCRCPY,
        "--no-audio",
        "--client-crop=1600:904:2017:510",
        "--always-on-top",
        "--window-width=1600",
        "--window-height=904",
        f"--render-driver={sdl_driver}",
    ]

    return subprocess.Popen(args, cwd=BIN_DIR)
