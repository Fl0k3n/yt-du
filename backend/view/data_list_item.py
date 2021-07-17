from abc import abstractmethod
from backend.utils.commands.command import Command
from PyQt5 import QtGui
from PyQt5.QtWidgets import QMenu, QWidget

# interface


class DataListItem(QWidget):
    HEIGHT = 100

    def __init__(self, show_details_command: Command, parent: QWidget):
        super().__init__(parent)
        self.setMinimumHeight(self.HEIGHT)
        self.setMaximumHeight(self.HEIGHT)
        self.show_details_command = show_details_command

    # @abstractmethod
    # def on_click(self):
    #     pass

    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
        if self.show_details_command:
            self.show_details_command.execute()

        return super().mouseDoubleClickEvent(a0)
