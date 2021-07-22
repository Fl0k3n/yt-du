from abc import abstractmethod
from backend.model.data_status import DataStatus
from backend.utils.commands.command import Command
from PyQt5.QtWidgets import QWidget
from view.data_list_item import DataListItem

# should derive from ABC, deleted because of metaclass conficts


class Displayable:
    @abstractmethod
    def to_data_list_item(self, show_details_command: Command, parent: QWidget) -> DataListItem:
        pass

    def get_status(self) -> DataStatus:
        return DataStatus(self.status)

    def set_status(self, status: DataStatus):
        self.status = status.value

    @abstractmethod
    def get_downloaded_bytes(self) -> int:
        pass

    @abstractmethod
    def get_size_bytes(self) -> int:
        pass
