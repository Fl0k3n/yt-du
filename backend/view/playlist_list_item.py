from backend.view.scrollable_label import ScrollableLabel
from backend.utils.commands.command import Command
from PyQt5.QtWidgets import QWidget
from backend.view.data_list_item import DataListItem


class PlaylistListItem(DataListItem):
    def __init__(self, name: str, url: str, directory_path: str,
                 status: str, show_details_command: Command, pause_command: Command,
                 resume_command: Command, is_pausable: bool, is_resumable: bool,
                 size: str = None, parent: QWidget = None):
        super().__init__(url=url, status=status, directory_path=directory_path,
                         show_details_command=show_details_command,
                         pause_command=pause_command, resume_command=resume_command,
                         is_pausable=is_pausable, is_resumable=is_resumable,
                         parent=parent)
        self.name = name

        self.name_label = ScrollableLabel(self, 300, 40, self.name)
        self.size_label = ScrollableLabel(
            self, 80, 40, '----' if size is None else size)
        self.speed_label = ScrollableLabel(self, 80, 40, '0 MB/s')
        self.add_to_layout(
            [self.name_label, self.status_label, self.progress_bar,
             self.size_label, self.speed_label])

    def set_dl_speed(self, speed_MBps: float):
        self.speed_label.setText(f'{speed_MBps} MB/s')

    def set_size(self, size: str):
        self.size_label.setText(size)
