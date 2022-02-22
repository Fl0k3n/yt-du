from typing import Iterable
from PyQt5 import Qt
from PyQt5.QtWidgets import QFrame, QListWidgetItem, QScrollArea, QListWidget, QHBoxLayout, QVBoxLayout, QLabel, QWidget
from backend.view.data_list_item import DataListItem


class DataSummaryBox(QFrame):
    def __init__(self, width: int, height: int):
        super().__init__()
        self.setFixedSize(width, height)
        self.inner_widget = QFrame()

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedSize(width, height)

        self.scroll_area.setWidget(self.inner_widget)

        self.visible_widgets = []

        self.inner_layout = QVBoxLayout()
        self.inner_layout.setSpacing(2)
        self.inner_widget.setLayout(self.inner_layout)

    def show_all(self, items: Iterable[DataListItem]):
        self._clear_list()

        for item in items:
            self.visible_widgets.append(item)
            self.inner_layout.addWidget(item)

    def append_top(self, item: DataListItem):
        # TODO
        self.show_all([item, *self.visible_widgets])

    def append(self, item: DataListItem):
        # TODO
        self.show_all([*self.visible_widgets, item])

    def delete_item(self, item: DataListItem):
        # TODO
        self.show_all([x for x in self.visible_widgets if x != item])

    def set_scrollable_size(self, size: int):
        self.inner_widget.setMinimumHeight(size)

    def _clear_list(self):
        for widget in self.visible_widgets:
            self.inner_layout.removeWidget(widget)
            widget.setParent(None)

        self.visible_widgets = []
