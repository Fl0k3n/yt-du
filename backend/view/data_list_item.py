from abc import abstractmethod
from backend.utils.util import open_dir_in_explorer
from PyQt5.QtCore import QPoint, Qt
from backend.utils.commands.command import CallRcvrCommand, Command
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QMenu, QWidget

# interface


class DataListItem(QWidget):
    HEIGHT = 100

    def __init__(self, url: str, directory_path: str, status: str,
                 show_details_command: Command, parent: QWidget):
        super().__init__(parent)
        self.url = url
        self.status = status
        self.directory_path = directory_path
        self.setMinimumHeight(self.HEIGHT)
        self.setMaximumHeight(self.HEIGHT)
        self.show_details_command = show_details_command

    # @abstractmethod
    # def on_click(self):
    #     pass

    def set_status(self, status: str):
        self.status = status

    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
        if self.show_details_command:
            self.show_details_command.execute()

        return super().mouseDoubleClickEvent(a0)

    def _show_menu_popup(self, pos: QPoint) -> QMenu:
        menu = QMenu(self)

        menu.addAction('Copy Url').triggered.connect(
            lambda: QApplication.clipboard().setText(self.url))

        menu.addAction('Open Location').triggered.connect(
            lambda: open_dir_in_explorer(
                self.directory_path,
                CallRcvrCommand(lambda: print('doesnt exist'))))

        menu.popup(pos)

        return menu

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        if a0.buttons() == Qt.RightButton:
            self._show_menu_popup(a0.screenPos().toPoint())

        return super().mousePressEvent(a0)
