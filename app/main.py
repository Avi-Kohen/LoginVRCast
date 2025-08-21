import sys
from PySide6.QtCore import Qt, QLocale
from PySide6.QtWidgets import QApplication, QMessageBox
from app.ui import MainWindow
from app.scrcpy_runner import status, wireless_auto, wireless_disconnect, start_scrcpy

_last_proc = None
_renderer = "OpenGL"
_crop_mode = "crop"   # ברירת מחדל לפי מה שהשתמשת בו עד עכשיו

_is_wireless = False  # אם יש לך כבר את הטוגל של חיבור/ניתוק

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
    global _last_proc, _renderer, _crop_mode
    _stop_if_running()
    try:
        _last_proc = start_scrcpy(_renderer, _crop_mode)
    except Exception as e:
        QMessageBox.critical(None, "שגיאה", f"שגיאה בהפעלה: {e}")

def on_stop():
    _stop_if_running()

def on_wireless(btn_widget):
    global _is_wireless
    if not _is_wireless:
        ok, msg = wireless_auto()
        if ok:
            _is_wireless = True
            btn_widget.setText("נתק אלחוטי")
            QMessageBox.information(None, "חיבור אלחוטי", msg)
        else:
            QMessageBox.warning(None, "חיבור אלחוטי", msg)
    else:
        ok, msg = wireless_disconnect()
        if ok:
            _is_wireless = False
            btn_widget.setText("חיבור אלחוטי")
            QMessageBox.information(None, "ניתוק אלחוטי", msg)
        else:
            QMessageBox.warning(None, "ניתוק אלחוטי", msg)

def on_renderer_changed(name: str):
    global _renderer
    _renderer = name  # ייכנס לתוקף בלחיצת "שידור" הבאה

def on_cropmode_changed(name: str):
    global _crop_mode
    _crop_mode = name  # "client-crop" או "crop", ייכנס לתוקף בלחיצת "שידור" הבאה

def get_status():
    s = status()
    if _last_proc and _last_proc.poll() is None:
        s["state"] = "casting"
        s["text"] = "משדר..."
    return s

def main():
    app = QApplication(sys.argv)
    QLocale.setDefault(QLocale(QLocale.Language.Hebrew, QLocale.Country.Israel))
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setApplicationName("LoginVRCast")
    w = MainWindow(on_cast, on_wireless, on_renderer_changed, on_cropmode_changed, on_stop, get_status)
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()