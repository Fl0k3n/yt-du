from PyQt5.QtWidgets import QFrame, QLabel, QWidget, QScrollArea
from PyQt5.QtCore import Qt


class ScrollableLabel(QScrollArea):
    def __init__(self, parent: QWidget, w: int, h: int, text: str) -> None:
        super().__init__(parent=parent)
        self.label = QLabel(text)
        self.setWidget(self.label)
        self.setFixedSize(w, h)
        self.setFrameStyle(QFrame.NoFrame)
        self.setAlignment(Qt.AlignCenter)

    def get_label(self) -> QLabel:
        return self.label

    def setText(self, text: str):
        self.label.setText(text)
