from PyQt5 import QtCore, QtGui
from backend.utils.commands.command import Command
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QWidget
from backend.view.options_box import OptionsBox
from backend.view.data_summary_box import DataSummaryBox
from backend.controller.gui.view_changer import DataViewChanger


class MainWindow(QDialog):
    _BACK_MOUSE_BTN = 8
    _FWD_MOUSE_BTN = 16

    def __init__(self, data_list: DataSummaryBox, view_changer: DataViewChanger,
                 playlist_added_cmd: Command, close_command: Command):
        super().__init__()
        self.setGeometry(200, 200, 800, 800)
        self.view_changer = view_changer
        self.close_command = close_command

        self.layout = QHBoxLayout(self)

        self.options = OptionsBox(playlist_added_cmd)
        self.layout.addWidget(self.options)
        self.data_list = data_list
        self.layout.addWidget(self.data_list)

        # setting parent to None removes Widget's content
        self.parent_holder = QWidget()

    def set_data_list(self, data_list: DataSummaryBox):
        self.layout.removeWidget(self.data_list)
        self.data_list.setParent(self.parent_holder)
        self.data_list = data_list
        self.layout.addWidget(self.data_list)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        btn = a0.button()
        if btn == self._BACK_MOUSE_BTN:
            self.view_changer.change_back()
        elif btn == self._FWD_MOUSE_BTN:
            self.view_changer.change_forward()

        return super().mousePressEvent(a0)

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        if a0.key() == QtCore.Qt.Key_Escape:
            self.close()
        return super().keyPressEvent(a0)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.close_command.execute()
        return super().closeEvent(a0)
