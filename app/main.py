import sys
from PySide6.QtCore import Qt, QLocale
from PySide6.QtWidgets import QApplication, QInputDialog
from app.ui import MainWindow
from app.scrcpy_runner import status, wireless_connect, start_scrcpy

_last_proc = None
_renderer = "OpenGL"  # ברירת מחדל

def on_cast():
    global _last_proc, _renderer
    try:
        _last_proc = start_scrcpy(_renderer)
    except Exception as e:
        print("שגיאה:", e)

def on_wireless():
    ip_port, ok = QInputDialog.getText(None, "חיבור אלחוטי", "הכנס IP:PORT (לדוגמה 192.168.1.50:5555):")
    if not ok or ":" not in ip_port:
        return
    code, ok2 = QInputDialog.getText(None, "צימוד (לא חובה)", "קוד צימוד (אם מופיע במסך ה-Quest):")
    code = code if ok2 and code.strip() else None
    rc = wireless_connect(ip_port.strip(), code)
    print("תוצאה:", "הצליח" if rc == 0 else f"נכשל ({rc})")

def on_renderer_changed(name: str):
    global _renderer
    # name מגיע מה-ComboBox ("OpenGL" / "Direct3D")
    _renderer = name

def get_status():
    s = status()
    if _last_proc and _last_proc.poll() is None:
        s["state"] = "casting"
        s["text"] = "משדר..."
    return s

def main():
    app = QApplication(sys.argv)
    QLocale.setDefault(QLocale(QLocale.Hebrew, QLocale.Israel))
    app.setLayoutDirection(Qt.RightToLeft)

    w = MainWindow(on_cast, on_wireless, on_renderer_changed, get_status)
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
