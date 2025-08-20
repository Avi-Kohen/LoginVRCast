import sys
from PySide6.QtCore import Qt, QLocale
from PySide6.QtWidgets import QApplication, QMessageBox
from app.ui import MainWindow
from app.scrcpy_runner import status, wireless_auto, start_scrcpy

_last_proc = None
_renderer = "OpenGL"  # default

def _stop_if_running():
    global _last_proc
    if _last_proc and _last_proc.poll() is None:
        _last_proc.terminate()
        try:
            _last_proc.wait(timeout=2)
        except Exception:
            _last_proc.kill()
        _last_proc = None

def on_cast():
    global _last_proc, _renderer
    _stop_if_running()
    try:
        _last_proc = start_scrcpy(_renderer)
    except Exception as e:
        QMessageBox.critical(None, "שגיאה", f"שגיאה בהפעלה: {e}")

def on_stop():
    _stop_if_running()

def on_wireless():
    ok, msg = wireless_auto()
    if ok:
        QMessageBox.information(None, "חיבור אלחוטי", msg)
    else:
        QMessageBox.warning(None, "חיבור אלחוטי", msg)

def on_renderer_changed(name: str):
    global _renderer
    _renderer = name  # applied on next "שידור"

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

    w = MainWindow(on_cast, on_wireless, on_renderer_changed, on_stop, get_status)
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
