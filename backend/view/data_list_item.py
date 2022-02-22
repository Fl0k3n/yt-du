from typing import Dict, Iterable, List
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
from PyQt5.QtWidgets import QAction, QApplication, QFrame, QGridLayout, QMenu, QProgressBar, QWidget
from backend.utils.property import Property
from backend.utils.util import open_dir_in_explorer
from backend.utils.commands.command import CallRcvrCommand, Command
from backend.view.scrollable_label import ScrollableLabel


class DataListItem(QFrame):
    HEIGHT = 80

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self._setup_default_properties()

        self._setup_gui_subcomponents()

        self._setup_status_label()

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedSize(150, 30)

        self.show_details_commands: List[Command] = []
        self.resume_commands: List[Command] = []
        self.pause_commands: List[Command] = []

        self.extra_menu_actions: Dict[str, QAction] = {}

        self._create_menu()

    def add_show_details_command(self, cmd: Command):
        self.show_details_commands.append(cmd)

    def add_pause_command(self, cmd: Command):
        self.pause_commands.append(cmd)

    def add_resume_command(self, cmd: Command):
        self.resume_commands.append(cmd)

    def _setup_default_properties(self):
        # those properties should be public and bindable
        self.url_property = Property[str]("no url")
        self.status_property = Property[str]("no status")
        self.directory_path_property = Property[str]("no path")
        self.is_pausable_property = Property[bool](False)
        self.is_resumable_property = Property[bool](False)
        self.progress_status_property = Property[float](0)

    def unbind_properties(self):
        for property in (self.url_property, self.status_property,
                         self.directory_path_property, self.is_pausable_property,
                         self.is_resumable_property):
            property.unbind_all()

    def _setup_status_label(self):
        self.status_label = ScrollableLabel(
            self, 120, 40, self.status_property.get())

        self.status_label.text_property.bind(self.status_property)

    def _setup_gui_subcomponents(self):
        self.setContentsMargins(0, 5, 0, 5)
        self.layout = QGridLayout(self)
        self.layout.setSpacing(10)

        self.setMinimumHeight(self.HEIGHT)
        self.setMaximumHeight(self.HEIGHT)
        self.setFrameStyle(1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedSize(150, 30)

        self.progress_status_property.add_property_changed_observer(
            callback=lambda _, new: self.update_progress_bar(new))

    def update_progress_bar(self, val: float):
        v = int(val * 100)
        self.progress_bar.setValue(v)

    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
        for cmd in self.show_details_commands:
            cmd.execute()

        return super().mouseDoubleClickEvent(a0)

    def _create_menu(self):
        self.menu = QMenu(self)

        self.menu.addAction('Copy Url').triggered.connect(
            lambda: QApplication.clipboard().setText(self.url_property.get()))

        self.menu.addAction('Open Location').triggered.connect(
            lambda: open_dir_in_explorer(
                self.directory_path_property.get(),
                CallRcvrCommand(lambda: print(f'{self.directory_path_property.get()} doesnt exist'))))

        self.pause_action = self._create_pause_action(
        ) if self.is_pausable_property.get() else None

        self.resume_action = self._create_resume_action(
        ) if self.is_resumable_property.get() else None

        self.is_pausable_property.add_property_changed_observer(
            callback=lambda _, new: self._toggle_pausable_action(new))

        self.is_resumable_property.add_property_changed_observer(
            callback=lambda _, new: self._toggle_resume_action(new))

    def _create_pause_action(self) -> QAction:
        return self._create_action('Pause', self.pause_commands)

    def _create_resume_action(self) -> QAction:
        return self._create_action('Resume', self.resume_commands)

    def _create_action(self, text: str, cmd_list: List[Command]) -> QAction:
        act = self.menu.addAction(text)

        def _run_cmds():
            for cmd in cmd_list:
                cmd.execute()

        act.triggered.connect(_run_cmds)

        return act

    def add_menu_item(self, text: str, cmd: Command) -> QAction:
        if text not in self.extra_menu_actions:
            self.extra_menu_actions[text] = self._create_action(text, cmd)

    def remove_menu_item(self, text: str):
        if text in self.extra_menu_actions:
            act = self.extra_menu_actions.pop(text)
            self.menu.removeAction(act)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        if a0.buttons() == Qt.RightButton:
            self.menu.popup(a0.screenPos().toPoint())

        return super().mousePressEvent(a0)

    def _add_to_layout(self, items: Iterable[QWidget]):
        for i, el in enumerate(items):
            self.layout.addWidget(el, 1, i + 1)

    def _toggle_pausable_action(self, pausable: bool):
        if pausable:
            if self.pause_action is None:
                self.pause_action = self._create_pause_action()
        else:
            if self.pause_action is not None:
                self.menu.removeAction(self.pause_action)
                self.pause_action = None

    def _toggle_resume_action(self, resumable: bool):
        if resumable:
            if self.resume_action is None:
                self.resume_action = self._create_resume_action()
        else:
            if self.resume_action is not None:
                self.menu.removeAction(self.resume_action)
                self.resume_action = None
