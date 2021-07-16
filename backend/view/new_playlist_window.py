from backend.utils.commands.command import Command
from PyQt5.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget


class NewPlaylistWindow(QDialog):
    def __init__(self, on_view_closed: Command, on_accepted: Command):
        super().__init__()
        self.on_view_closed = on_view_closed
        self.setGeometry(200, 200, 400, 400)

        self.layout = QVBoxLayout(self)

        options_box = QWidget()
        grid_layout = QGridLayout(options_box)

        self.layout.addWidget(options_box)

        self.inputs = [QLineEdit() for _ in range(3)]
        labels = [QLabel(x) for x in ['url', 'name', 'path']]

        for i, (lab, inp) in enumerate(zip(labels, self.inputs)):
            grid_layout.addWidget(lab, i+1, 1)
            grid_layout.addWidget(inp, i+1, 2)

        self.url_input, self.name_input, self.path_input = self.inputs

        btn_box = QWidget()
        self.layout.addWidget(btn_box)

        inner_layout = QHBoxLayout(btn_box)

        self.add_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")

        self.add_btn.clicked.connect(lambda: on_accepted.execute())
        self.cancel_btn.clicked.connect(lambda: self.close())

        for btn in [self.add_btn, self.cancel_btn]:
            inner_layout.addWidget(btn)

    def get_inputs(self):
        return self.inputs

    def closeEvent(self, a0):
        self.on_view_closed.execute()
        return super().closeEvent(a0)
