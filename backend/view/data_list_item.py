from abc import abstractmethod
from PyQt5.QtWidgets import QMenu, QWidget

# interface


class DataListItem(QWidget):
    HEIGHT = 100

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setMinimumHeight(self.HEIGHT)
        self.setMaximumHeight(self.HEIGHT)

    # @abstractmethod
    # def on_click(self):
    #     pass
