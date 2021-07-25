from backend.view.scrollable_label import ScrollableLabel
from backend.utils.commands.command import Command
from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QWidget, QProgressBar
from view.data_list_item import DataListItem


class PlaylistListItem(DataListItem):
    def __init__(self, name: str, url: str, directory_path: str,
                 status: str, show_details_command: Command, pause_command: Command,
                 resume_command: Command, is_pausable: bool, is_resumable: bool,
                 parent: QWidget = None):
        super().__init__(url=url, status=status, directory_path=directory_path,
                         show_details_command=show_details_command,
                         pause_command=pause_command, resume_command=resume_command,
                         is_pausable=is_pausable, is_resumable=is_resumable,
                         parent=parent)
        self.name = name

        self.name_label = ScrollableLabel(self, 300, 40, self.name)
        self.add_to_layout(
            [self.name_label, self.status_label, self.progress_bar])
