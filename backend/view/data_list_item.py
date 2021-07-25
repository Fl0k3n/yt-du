from typing import Iterable
from backend.utils.util import open_dir_in_explorer
from PyQt5.QtCore import Qt
from backend.utils.commands.command import CallRcvrCommand, Command
from PyQt5 import QtGui
from PyQt5.QtWidgets import QAction, QApplication, QFrame, QGridLayout, QMenu, QProgressBar, QWidget
from view.scrollable_label import ScrollableLabel


class DataListItem(QFrame):
    HEIGHT = 80

    def __init__(self, url: str, directory_path: str, status: str,
                 show_details_command: Command, pause_command: Command,
                 resume_command: Command, is_pausable: bool, is_resumable: bool,
                 parent: QWidget):
        super().__init__(parent)
        self.url = url
        self.status = status
        self.directory_path = directory_path
        self.is_pausable = is_pausable
        self.is_resumable = is_resumable

        self.setContentsMargins(0, 5, 0, 5)
        self.layout = QGridLayout(self)
        self.layout.setSpacing(10)

        self.setMinimumHeight(self.HEIGHT)
        self.setMaximumHeight(self.HEIGHT)
        self.setFrameStyle(1)

        self.show_details_command = show_details_command
        self.pause_command = pause_command
        self.resume_command = resume_command

        self.status_label = ScrollableLabel(self, 120, 40, self.status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedSize(150, 30)

        self._create_menu()

    def update_progress_bar(self, val: float):
        v = int(val * 100)
        self.progress_bar.setValue(v)

    def set_status(self, status: str):
        self.status = status
        self.status_label.setText(status)

    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
        if self.show_details_command:
            self.show_details_command.execute()

        return super().mouseDoubleClickEvent(a0)

    def _create_menu(self):
        self.menu = QMenu(self)

        self.menu.addAction('Copy Url').triggered.connect(
            lambda: QApplication.clipboard().setText(self.url))

        self.menu.addAction('Open Location').triggered.connect(
            lambda: open_dir_in_explorer(
                self.directory_path,
                CallRcvrCommand(lambda: print('doesnt exist'))))

        self.pause_action = self._create_pause_action() if self.is_pausable else None

        self.resume_action = self._create_resume_action() if self.is_resumable else None

    def _create_pause_action(self) -> QAction:
        return self._create_action('Pause', self.pause_command)

    def _create_resume_action(self) -> QAction:
        return self._create_action('Resume', self.resume_command)

    def _create_action(self, text: str, cmd: Command) -> QAction:
        act = self.menu.addAction(text)
        act.triggered.connect(lambda: cmd.execute())
        return act

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        if a0.buttons() == Qt.RightButton:
            self.menu.popup(a0.screenPos().toPoint())

        return super().mousePressEvent(a0)

    def add_to_layout(self, items: Iterable[QWidget]):
        for i, el in enumerate(items):
            self.layout.addWidget(el, 1, i + 1)

    def set_pausable(self, pausable: bool):
        print('setting pausable to ', pausable)
        self.is_pausable = pausable
        if self.is_pausable:
            if self.pause_action is None:
                self.pause_action = self._create_pause_action()
        else:
            if self.pause_action is not None:
                print('removing action')
                self.menu.removeAction(self.pause_action)
                self.pause_action = None

    def set_resumable(self, resumable: bool):
        self.is_resumable = resumable
        if self.is_resumable:
            if self.resume_action is None:
                self.resume_action = self._create_resume_action()
        else:
            if self.resume_action is not None:
                self.menu.removeAction(self.resume_action)
                self.resume_action = None
