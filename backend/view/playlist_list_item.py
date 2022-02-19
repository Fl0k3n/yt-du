from backend.utils.property import Property
from backend.view.scrollable_label import ScrollableLabel
from backend.utils.commands.command import Command
from PyQt5.QtWidgets import QWidget
from backend.view.data_list_item import DataListItem


class PlaylistListItem(DataListItem):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self.name_property = Property("no name")
        self.size_property = Property("----")
        self.speed_property = Property("0 MB/s")

        self.name_label = ScrollableLabel(
            self, 300, 40, self.name_property.get())
        self.name_label.text_property.bind(self.name_property)

        self.size_label = ScrollableLabel(
            self, 80, 40, self.size_property.get())
        self.size_label.text_property.bind(self.size_property)

        self.speed_label = ScrollableLabel(
            self, 80, 40, self.speed_property.get())
        self.speed_label.text_property.bind(self.speed_property)

        self.add_to_layout(
            [self.name_label, self.status_label, self.progress_bar,
             self.size_label, self.speed_label])
