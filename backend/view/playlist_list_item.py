from backend.utils.commands.command import Command
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QWidget, QProgressBar
from view.data_list_item import DataListItem


class PlaylistListItem(DataListItem):
    def __init__(self, name: str, url: str, directory_path: str,
                 status: str = 'new', show_details_command: Command = None, parent: QWidget = None):
        super().__init__(url=url, status=status, directory_path=directory_path,
                         show_details_command=show_details_command, parent=parent)
        self.name = name

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(QLabel(self.name))
        self.layout.addWidget(QLabel(self.status))

        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)
        self.dl_status = 100

        self.progress_bar.setValue(self.dl_status)
