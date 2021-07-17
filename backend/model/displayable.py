from abc import abstractmethod
from backend.utils.commands.command import Command
from PyQt5.QtWidgets import QWidget
from view.data_list_item import DataListItem

# should derive from ABC, deleated because of metaclass conficts


class Displayable:
    @abstractmethod
    def to_data_list_item(self, show_details_command: Command, parent: QWidget) -> DataListItem:
        pass
