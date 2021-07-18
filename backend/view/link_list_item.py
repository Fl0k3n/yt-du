from backend.utils.commands.command import Command
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QWidget, QProgressBar
from view.data_list_item import DataListItem


class LinkListItem(DataListItem):
    def __init__(self, playlist_idx: int, name: str, url: str, directory_path: str,
                 show_details_command: Command = None, parent: QWidget = None):
        super().__init__(url=url, directory_path=directory_path,
                         show_details_command=show_details_command, parent=parent)
        self.name = name
        self.playlist_idx = playlist_idx

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(QLabel(str(self.playlist_idx)))
        self.layout.addWidget(QLabel(self.name))

        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)
        self.dl_status = 100

        self.progress_bar.setValue(self.dl_status)
