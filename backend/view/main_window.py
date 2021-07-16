from backend.utils.commands.command import Command
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout
from view.options_box import OptionsBox
from view.data_summary_box import DataSummaryBox


class MainWindow(QDialog):
    def __init__(self, playlist_added_cmd: Command):
        super().__init__()
        self.setGeometry(200, 200, 800, 800)

        self.layout = QHBoxLayout(self)

        self.options = OptionsBox(playlist_added_cmd)
        self.data_list = DataSummaryBox(self)

        self.layout.addWidget(self.options)
        self.layout.addWidget(self.data_list)
