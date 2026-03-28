from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QApplication
)
from PyQt6.QtCore import Qt


class InputOverlay(QDialog):
    def __init__(self, mode="text"):
        super().__init__()
        self.result = None
        self.mode = mode

        # window setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFixedSize(620, 110)
        self.setStyleSheet("background-color: #1a1a1a; border-radius: 12px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(8)

        if mode == "text":
            self._build_text(layout)
        else:
            self._build_voice(layout)

        self._center()

    def _build_text(self, layout):
        label = QLabel("What do you want to do?")
        label.setStyleSheet("color: #888888; font-size: 13px;")
        layout.addWidget(label)

        self.input_field = QLineEdit()
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                color: #ffffff;
                font-size: 20px;
                padding: 6px 10px;
                border: 2px solid #444444;
                border-radius: 8px;
            }
            QLineEdit:focus {
                border: 2px solid #666666;
            }
        """)
        self.input_field.setPlaceholderText("e.g.  send email to Marko im late...")
        self.input_field.returnPressed.connect(self._on_enter)
        layout.addWidget(self.input_field)

    def _build_voice(self, layout):
        label = QLabel("🎤  Listening...")
        label.setStyleSheet("color: #ffffff; font-size: 28px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        hint = QLabel("ESC to cancel")
        hint.setStyleSheet("color: #555555; font-size: 11px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

    def _on_enter(self):
        text = self.input_field.text().strip()
        if text:
            self.result = text
            self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.result = None
            self.reject()

    def _center(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2 - 80
        self.move(x, y)