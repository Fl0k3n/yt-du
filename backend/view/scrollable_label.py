from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QLabel, QWidget, QScrollArea
from backend.utils.property import Property


class ScrollableLabel(QScrollArea):
    def __init__(self, parent: QWidget, w: int, h: int, text: str) -> None:
        super().__init__(parent=parent)
        self.text_property = Property[str](text)

        self.text_property.add_property_changed_observer(
            callback=lambda _, new: self.setText(new))

        self.setText(text)
        self.setFixedSize(w, h)
        self.setFrameStyle(QFrame.NoFrame)
        self.setAlignment(Qt.AlignCenter)

    def setText(self, text: str):
        self.label = QLabel(text)
        self.setWidget(self.label)

    def text(self) -> str:
        return self.label.text()
