from abc import abstractmethod
from backend.model.data_status import DataStatus
from backend.utils.commands.command import Command
from PyQt5.QtWidgets import QWidget
from backend.view.data_list_item import DataListItem

# should derive from ABC, deleted because of metaclass conficts


class Downloadable:
    @abstractmethod
    def to_data_list_item(self, show_details_command: Command,
                          pause_command: Command, resume_command: Command,
                          is_pausable: bool, is_resumable: bool,
                          parent: QWidget) -> DataListItem:
        pass

    @abstractmethod
    def get_downloaded_bytes(self) -> int:
        pass

    @abstractmethod
    def get_size_bytes(self) -> int:
        pass

    @abstractmethod
    def get_status(self) -> DataStatus:
        pass

    @abstractmethod
    def set_status(self, status: DataStatus):
        pass

    # @abstractmethod
    # def get_url(self) -> str:
    #     pass

    # @abstractmethod
    # def get_path(self) -> str:
    #     pass

    # @abstractmethod
    # def is_pausable(self) -> bool:
    #     pass

    # @abstractmethod
    # def is_resumable(self) -> bool:
    #     pass

    # @abstractmethod
    # def is_removable(self) -> bool:
    #     pass

    # @abstractmethod
    # def is_paused(self) -> bool:
    #     pass

    # @abstractmethod
    # def is_finished(self) -> bool:
    #     pass

    def get_formatted_size(self) -> str:
        size_bytes = self.get_size_bytes()

        if size_bytes > 1073741824:  # GB
            size = f'{round(size_bytes / 1073741824 * 100) / 100} GB'
        else:
            size = f'{round(size_bytes / 1048576 * 100) / 100} MB'

        return size
