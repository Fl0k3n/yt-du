from PyQt5.QtWidgets import QFrame, QListWidgetItem, QScrollArea, QListWidget, QHBoxLayout, QVBoxLayout, QLabel


class DataSummaryBox(QFrame):
    def __init__(self, parent):
        super().__init__()

        self.setGeometry(100, 50, 600, 500)
        self.scroll_area = QScrollArea(self)
        l = QListWidget()
        self.scroll_area.setWidget(l)

        for msg in ['sdgsdgsdog', 'sdgsdgsdgsdg', 'sdgsdgsdgs', 'sdgsdgsdgsdg', 'sdgsdgsdgs', 'sdgsdgsdgsdg', 'sdgsdgsdgs', 'sdgsdgsdgsdg', 'sdgsdgsdgs', 'sdgsdgsdgsdg', 'sdgsdgsdgs', 'sdgsdgsdgsdg', 'sdgsdgsdgs', 'sdgsdgsdgsdg', 'sdgsdgsdgs', 'sdgsdgsdgsdg', 'sdgsdgsdgs', 'sdgsdgsdgsdg', 'sdgsdgsdgs', 'sdgsdgsdgsdg', 'sdgsdgsdgs', 'sdgsdgsdgsdg', 'sdgsdgsdgs']:
            l.addItem(QListWidgetItem(msg))
