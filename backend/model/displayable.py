from abc import abstractmethod
from PyQt5.QtWidgets import QWidget
from view.data_list_item import DataListItem

# should derive from ABC, deleated because of metaclass conficts


class Displayable:
    @abstractmethod
    def to_data_list_item(self, parent: QWidget) -> DataListItem:
        pass
