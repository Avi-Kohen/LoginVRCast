from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtWidgets import (
    QWidget, QMainWindow, QPushButton, QLabel, QComboBox, QHBoxLayout,
    QVBoxLayout, QApplication, QFrame
)

class StatusLight(QFrame):
    # נורית חיווי: אדום/צהוב/ירוק
    def __init__(self, color="red"):
        super().__init__()
        self.setFixedSize(QSize(16, 16))
        self.setStyleSheet("border-radius: 8px; background: red;")
        self.setColor(color)

    def setColor(self, color: str):
        color = color.lower()
        palette = {
            "red":    "#e94242",
            "yellow": "#f0c52e",
            "green":  "#38c172",
            "gray":   "#9aa0a6",
        }
        self.setStyleSheet(f"border-radius: 8px; background: {palette.get(color, '#9aa0a6')};")

class MainWindow(QMainWindow):
    def __init__(self, on_cast, on_wireless, on_preset_changed, get_status):
        super().__init__()
        self.setWindowTitle("LoginVRCast")
        self.setMinimumSize(560, 220)

        # כיווניות ימין-לשמאל
        self.setLayoutDirection(Qt.RightToLeft)

        # כפתורים
        self.cast_btn = QPushButton("שידור")
        self.wireless_btn = QPushButton("חיבור אלחוטי")

        # פרופילים
        self.preset = QComboBox()
        self.preset.addItems(["נמוך", "בינוני", "גבוה"])

        # סטטוס
        self.status_light = StatusLight("red")
        self.status_label = QLabel("מכשיר לא מחובר")

        # סידור ראשי
        top = QHBoxLayout()
        top.addWidget(self.cast_btn)
        top.addWidget(self.wireless_btn)
        top.addStretch(1)

        mid = QHBoxLayout()
        mid.addWidget(QLabel("פרופיל:"))
        mid.addWidget(self.preset)
        mid.addStretch(1)

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

        # חיבור חיוויים
        self.cast_btn.clicked.connect(on_cast)
        self.wireless_btn.clicked.connect(on_wireless)
        self.preset.currentTextChanged.connect(on_preset_changed)

        # רענון סטטוס כל 2 שניות
        self._get_status = get_status
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_status)
        self._timer.start(2000)
        self.refresh_status()

    def refresh_status(self):
        s = self._get_status()
        # s = {"state": "none|pairing|ready|casting", "text": "..."}
        if s["state"] in ("ready", "casting"):
            self.status_light.setColor("green")
        elif s["state"] == "pairing":
            self.status_light.setColor("yellow")
        else:
            self.status_light.setColor("red")
        self.status_label.setText(s["text"])
