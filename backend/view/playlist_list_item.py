from backend.utils.commands.command import CallRcvrCommand
from PyQt5 import QtGui
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QMenu, QWidget, QApplication
from view.data_list_item import DataListItem
from PyQt5.QtCore import QPoint, Qt
from utils.util import open_dir_in_explorer


class PlaylistListItem(DataListItem):
    def __init__(self, name: str, url: str, directory_path: str,
                 parent: QWidget = None):
        super().__init__(parent=parent)
        self.url = url
        self.name = name
        self.directory_path = directory_path

        self.layout = QHBoxLayout(self)

        for x in [name, url, directory_path]:
            self.layout.addWidget(QLabel(x))

    def _show_menu_popup(self, pos: QPoint):
        menu = QMenu(self)

        menu.addAction('Copy Url').triggered.connect(
            lambda: QApplication.clipboard().setText(self.url))

        menu.addAction('Open Location').triggered.connect(
            lambda: open_dir_in_explorer(
                self.directory_path,
                CallRcvrCommand(lambda: print('doesnt exist'))))

        menu.popup(pos)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        if a0.buttons() == Qt.RightButton:
            self._show_menu_popup(a0.screenPos().toPoint())

        return super().mousePressEvent(a0)
