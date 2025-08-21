from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtWidgets import (
    QWidget, QMainWindow, QPushButton, QLabel, QHBoxLayout,
    QVBoxLayout, QApplication, QFrame, QComboBox, QMenuBar, QMenu,
    QTextBrowser, QMessageBox
)
from PySide6.QtGui import QIcon, QAction

class HelpWindow(QWidget):
    def __init__(self, title: str, html: str, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setWindowTitle(title)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(560, 460)

        self.view = QTextBrowser(self)
        self.view.setOpenExternalLinks(True)
        self.view.setHtml(
            f"""
            <html dir="rtl">
              <head>
                <meta charset="utf-8">
                <style>
                  body {{ font-family: Segoe UI, Arial, sans-serif; line-height: 1.5; }}
                  h1, h2 {{ margin: 0.4em 0; }}
                  ol, ul {{ padding-inline-start: 20px; }}
                  code {{ background:#f3f3f3; padding:2px 4px; border-radius:4px; }}
                  .note {{ background:#fff8d8; border:1px solid #f0e0a0; padding:8px; border-radius:8px; }}
                </style>
              </head>
              <body>{html}</body>
            </html>
            """
        )

        root = QVBoxLayout(self)
        root.addWidget(self.view)

class StatusLight(QFrame):
    def __init__(self, color="red"):
        super().__init__()
        self.setFixedSize(QSize(16, 16))
        self.setColor(color)

    def setColor(self, color: str):
        palette = {
            "red":    "#e94242",
            "yellow": "#f0c52e",
            "green":  "#38c172",
            "gray":   "#9aa0a6",
        }
        self.setStyleSheet(f"border-radius: 8px; background: {palette.get(color, '#9aa0a6')};")

class MainWindow(QMainWindow):
    def __init__(self, on_cast, on_wireless, on_renderer_changed, on_cropmode_changed, on_stop, get_status):
        super().__init__()
        self.setWindowTitle("LoginVRCast")
        self.setMinimumSize(400, 210)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowIcon(QIcon("icon.ico"))
        # כפתורים
        self.cast_btn = QPushButton("שידור")
        self.stop_btn = QPushButton("עצור")
        self.wireless_btn = QPushButton("חיבור אלחוטי")

        # בוררי מנוע/חיתוך
        self.renderer_combo = QComboBox()
        self.renderer_combo.addItems(["OpenGL", "Direct3D"])

        self.cropmode_combo = QComboBox()
        self.cropmode_combo.addItems([ "crop","client-crop"])  # ברירת מחדל: client-crop למי שמעדיף 1:1, אך נוכל לשנות בהמשך

        # סטטוס
        self.status_light = StatusLight("red")
        self.status_label = QLabel("מכשיר לא מחובר")
        
        self._help_windows = []

        # === תפריט עליון ===
        menubar: QMenuBar = self.menuBar()
        menubar.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # קובץ
        file_menu = menubar.addMenu("קובץ")
        act_exit = QAction("יציאה", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # עזרה
        help_menu = menubar.addMenu("עזרה")

        act_howto = QAction("הוראות", self)
        act_howto.triggered.connect(self.show_instructions)
        help_menu.addAction(act_howto)

        act_faq = QAction("שאלות נפוצות (FAQ)", self)
        act_faq.triggered.connect(self.show_faq)
        help_menu.addAction(act_faq)

        act_about = QAction("אודות", self)
        act_about.triggered.connect(self.show_about)
        help_menu.addAction(act_about)

        # שורה עליונה
        top = QHBoxLayout()
        top.addWidget(self.cast_btn)
        top.addWidget(self.stop_btn)
        top.addWidget(self.wireless_btn)
        top.addStretch(1)

        # שורת הגדרות
        mid = QHBoxLayout()
        mid.addWidget(QLabel("מנוע גרפי:"))
        mid.addWidget(self.renderer_combo)
        mid.addSpacing(16)
        mid.addWidget(QLabel("מצב חיתוך:"))
        mid.addWidget(self.cropmode_combo)
        mid.addStretch(1)

        # סטטוס
        status = QHBoxLayout()
        status.addWidget(QLabel("מצב:"))
        status.addWidget(self.status_light)
        status.addWidget(self.status_label)
        status.addStretch(1)

        root = QVBoxLayout()
        root.addLayout(top)
        root.addSpacing(8)
        root.addLayout(mid)
        root.addSpacing(8)
        root.addLayout(status)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

        # חיבורים
        self.cast_btn.clicked.connect(on_cast)
        self.stop_btn.clicked.connect(on_stop)
        self.wireless_btn.clicked.connect(lambda: on_wireless(self.wireless_btn))
        self.renderer_combo.currentTextChanged.connect(on_renderer_changed)
        self.cropmode_combo.currentTextChanged.connect(on_cropmode_changed)

        # רענון סטטוס
        self._get_status = get_status
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_status)
        self._timer.start(2000)
        self.refresh_status()


    def refresh_status(self):
        s = self._get_status()
        if s["state"] in ("ready", "casting"):
            self.status_light.setColor("green")
        elif s["state"] == "pairing":
            self.status_light.setColor("yellow")
        else:
            self.status_light.setColor("red")
        self.status_label.setText(s["text"])

    # ====== עזרה ======
    def show_instructions(self):
        html = """
        <h1>הוראות שימוש – LoginVRCast</h1>
        <ol>
          <li>הדלק את ה‑<b>Meta Quest</b> וודא שמצב מפתח (Developer Mode) פעיל.</li>
          <li>חבר את הקווסט למחשב באמצעות <b>כבל USB</b>.</li>
          <li>במסך המכשיר אשר <b>USB debugging</b> ולחץ <b>Always allow</b>.</li>
          <li>בחלון התוכנה לחץ <b>שידור</b> כדי להתחיל הצגה.</li>
          <li>רוצה לעבוד בלי כבל? לחץ <b>חיבור אלחוטי</b> — אם ההתחברות מצליחה, אפשר לנתק את ה‑USB.</li>
        </ol>

        <h2>טיפים</h2>
        <ul>
          <li>אם החיבור האלחוטי נכשל — ודא שהמחשב וה‑Quest באותה רשת Wi‑Fi.</li>
          <li>בחר <b>מנוע גרפע</b> (OpenGL/Direct3D) לפי מה שעובד חלק יותר אצלך.</li>
          <li>בחר מצב <b>מצב חיתוך</b>: client-crop או crop בהתאם לצורך.</li>
        </ul>

        <h2>קיצורים</h2>
        <ul>
          <li><b>מסך מלא</b> — alt + F </li>
          <li><b>רענון</b> — alt + shift + R .</li>
        </ul>
        """
        self._open_help("הוראות", html)

    def show_faq(self):
        html = """
        <h1>שאלות נפוצות (FAQ)</h1>

        <h2>איך מפעילים מצב מפתח?</h2>
        <p>
          מדריך וידאו:
          <a href="https://drive.google.com/file/d/1hYf4B3nKVmHpBGViHWfdY_qgfD-LOKPg/view?usp=drive_link">
            לחץ כאן
          </a>
        </p>

        <h2>חיבור אלחוטי לא מצליח</h2>
        <ul>
          <li>ודא שה‑PC וה‑Quest על אותה רשת.</li>
          <li>חבר USB, אשר Debug, ואז לחץ שוב "חיבור אלחוטי".</li>
        </ul>
        
        <h2>המסך מרצד?</h2>
        <ul>
          <li>נסה לשנות את <b>מצב חיתוך</b> ל־client-crop או crop בתפריט.
          זה יכול לשפר את התצוגה.
          </li>
          <li>alt + shift + R מרענן את התצוגה.</li>
        </ul>

        <h2>יצירת קשר</h2>
        <p>
          מייל תמיכה:
          <a href="mailto:info@loginvr.co.il?subject=%D7%90%D7%A4%D7%9C%D7%99%D7%A7%D7%A6%D7%99%D7%99%D7%AA%20%D7%A7%D7%90%D7%A1%D7%98%D7%99%D7%A0%D7%92&body=%D7%94%D7%99%2C%0A%0A%D7%90%D7%A0%D7%99%20%D7%A6%D7%A8%D7%99%D7%9A%20%D7%A2%D7%96%D7%A8%D7%94%20%D7%A2%D7%9D%E2%80%A6">
            info@loginvr.co.il
          </a>
        </p>
        """
        self._open_help("FAQ / Help", html)

    def show_about(self):
        html = """
        <h1>אודות</h1>
        <p><b>LoginVRCast</b> — כלי לשיקוף מכשירי <b>Meta Quest</b> למחשב Windows באמצעות scrcpy, עם ממשק בעברית.</p>
        <p>נוצר על ידי <b>Avi Kohen</b> · 2025 · גרסה v0.2.0</p>
        <p>All rights reserved to LoginVR — internal use only.</p>
        """
        self._open_help("אודות", html)

    def _open_help(self, title: str, html: str):
        # פותחים כחלון עליון עצמאי (parent=None)
        w = HelpWindow(title, html, parent=None)
        w.show()
        # שומרים רפרנס כדי שה־GC לא יסגור אותו
        self._help_windows.append(w)
        # אופציונלי: נקה מהרשימה כשנסגר
        w.destroyed.connect(lambda *_: self._help_windows.remove(w) if w in self._help_windows else None)