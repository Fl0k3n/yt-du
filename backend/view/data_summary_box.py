from typing import Iterable
from PyQt5.QtWidgets import QFrame, QListWidgetItem, QScrollArea, QListWidget, QHBoxLayout, QVBoxLayout, QLabel, QWidget
from PyQt5 import Qt
from view.data_list_item import DataListItem


class DataSummaryBox(QFrame):
    def __init__(self, container: QWidget, width: int, height: int):
        super().__init__()
        self.contaier = container

        self.scroll_area = QScrollArea(container)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedSize(width, height)

        self.scroll_area.setWidget(self)

        self.visible_widgets = []

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def show_all(self, items: Iterable[DataListItem]):
        self._clear_list()

        for item in items:
            self.visible_widgets.append(item)
            self.layout.addWidget(item)

    def set_item_count(self, item_count: int):
        self.setMinimumHeight(DataListItem.HEIGHT * item_count)

    def _clear_list(self):
        for widget in self.visible_widgets:
            self.layout.removeWidget(widget)
            widget.setParent(None)

        self.visible_widgets = []
