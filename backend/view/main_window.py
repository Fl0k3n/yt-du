from PyQt5 import QtGui
from backend.utils.commands.command import Command
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QWidget
from view.options_box import OptionsBox
from view.data_summary_box import DataSummaryBox
from controller.gui.view_changer import DataViewChanger


class MainWindow(QDialog):
    _BACK_MOUSE_BTN = 8
    _FWD_MOUSE_BTN = 16

    def __init__(self, data_list: DataSummaryBox, view_changer: DataViewChanger,
                 playlist_added_cmd: Command):
        super().__init__()
        self.setGeometry(200, 200, 800, 800)
        self.view_changer = view_changer

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
