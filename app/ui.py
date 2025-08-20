from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtWidgets import (
    QWidget, QMainWindow, QPushButton, QLabel, QHBoxLayout,
    QVBoxLayout, QApplication, QFrame, QComboBox
)

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
    def __init__(self, on_cast, on_wireless, on_renderer_changed, on_stop, get_status):
        super().__init__()
        self.setWindowTitle("LoginVRCast")
        self.setMinimumSize(600, 210)
        self.setLayoutDirection(Qt.RightToLeft)
        

        # כפתורים
        self.cast_btn = QPushButton("שידור")
        self.stop_btn = QPushButton("עצור")
        self.wireless_btn = QPushButton("חיבור אלחוטי")

        # בורר מנוע גרפי
        self.renderer_combo = QComboBox()
        self.renderer_combo.addItems(["OpenGL", "Direct3D"])

        # סטטוס
        self.status_light = StatusLight("red")
        self.status_label = QLabel("מכשיר לא מחובר")

        # שורה עליונה: שידור/עצור/אלחוטי
        top = QHBoxLayout()
        top.addWidget(self.cast_btn)
        top.addWidget(self.stop_btn)
        top.addWidget(self.wireless_btn)
        top.addStretch(1)

        # שורת הגדרות: מנוע גרפי
        mid = QHBoxLayout()
        mid.addWidget(QLabel("מנוע גרפי:"))
        mid.addWidget(self.renderer_combo)
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
