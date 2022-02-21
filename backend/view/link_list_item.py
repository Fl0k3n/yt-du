from PyQt5.QtWidgets import QWidget
from backend.utils.property import Property
from backend.view.data_list_item import DataListItem
from backend.view.scrollable_label import ScrollableLabel


class LinkListItem(DataListItem):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self.name_property = Property[str]("no name")
        self.playlist_idx_property = Property[str]("no playlist_idx")

        self.name_label = ScrollableLabel(
            self, 300, 40, self.name_property.get())
        self.idx_label = ScrollableLabel(
            self, 40, 40, self.playlist_idx_property.get())

        self.name_label.text_property.bind(self.name_property)
        self.idx_label.text_property.bind(self.playlist_idx_property)

        self._add_to_layout([self.idx_label, self.name_label,
                             self.status_label, self.progress_bar])

    def unbind_properties(self):
        super().unbind_properties()
        for property in (self.name_property, self.playlist_idx_property):
            property.unbind_all()
