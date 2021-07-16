from backend.utils.commands.command import Command
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QWidget
from view.options_box import OptionsBox
from view.data_summary_box import DataSummaryBox


class MainWindow(QDialog):
    def __init__(self, playlist_added_cmd: Command):
        super().__init__()
        self.setGeometry(200, 200, 800, 800)

        self.layout = QHBoxLayout(self)

        self.options = OptionsBox(playlist_added_cmd)
        self.layout.addWidget(self.options)

        self._create_data_summary_box()

    def _create_data_summary_box(self):
        container = QWidget()
        container.setFixedSize(600, 600)
        self.data_list = DataSummaryBox(container, 600, 600)
        self.layout.addWidget(container)

    def get_data_list(self) -> DataSummaryBox:
        return self.data_list
