from PyQt5.QtWidgets import QFrame, QLabel, QWidget, QScrollArea
from PyQt5.QtCore import Qt


class ScrollableLabel(QScrollArea):
    def __init__(self, parent: QWidget, w: int, h: int, text: str) -> None:
        super().__init__(parent=parent)
        self.setText(text)
        self.setFixedSize(w, h)
        self.setFrameStyle(QFrame.NoFrame)
        self.setAlignment(Qt.AlignCenter)

    def setText(self, text: str):
        self.label = QLabel(text)
        self.setWidget(self.label)
