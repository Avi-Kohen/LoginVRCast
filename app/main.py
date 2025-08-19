import sys
from PySide6.QtCore import Qt, QLocale
from PySide6.QtWidgets import QApplication, QInputDialog
from app.ui import MainWindow
from app.scrcpy_runner import status, wireless_connect, start_scrcpy, PRESETS

# מצב פשוט
_current_preset = "בינוני"
_last_proc = None

def on_cast():
    global _last_proc
    try:
        _last_proc = start_scrcpy(_current_preset)
    except Exception as e:
        print("שגיאה:", e)

def on_wireless():
    # במקום קונסול - דיאלוגים בעברית
    ip_port, ok = QInputDialog.getText(None, "חיבור אלחוטי", "הכנס IP:PORT (לדוגמה 192.168.1.50:5555):")
    if not ok or ":" not in ip_port:
        return
    code, ok2 = QInputDialog.getText(None, "צימוד (לא חובה)", "קוד צימוד (אם מופיע במסך ה-Quest):")
    code = code if ok2 and code.strip() else None
    rc = wireless_connect(ip_port.strip(), code)
    if rc == 0:
        QInputDialog.getText(None, "תוצאה", "החיבור הצליח. לחץ אישור להמשך.")
    else:
        QInputDialog.getText(None, "תוצאה", f"החיבור נכשל (קוד {rc}). בדוק שה‑Wireless debugging פעיל.")

def on_preset_changed(name: str):
    global _current_preset
    if name in PRESETS:
        _current_preset = name

def get_status():
    s = status()
    if _last_proc and _last_proc.poll() is None:
        s["state"] = "casting"
        s["text"] = s["text"].replace("מכשיר מזוהה", "משדר")
    return s

def main():
    app = QApplication(sys.argv)
    # לוקייל עברי וכיווניות גלובלית
    QLocale.setDefault(QLocale(QLocale.Hebrew, QLocale.Israel))
    app.setLayoutDirection(Qt.RightToLeft)

    w = MainWindow(on_cast, on_wireless, on_preset_changed, get_status)
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
