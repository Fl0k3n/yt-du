from backend.view.scrollable_label import ScrollableLabel
from backend.utils.commands.command import Command
from PyQt5.QtWidgets import QDialog, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
from backend.utils.assets_loader import AssetsLoader as AL
from PyQt5.QtCore import Qt


class NewPlaylistWindow(QDialog):
    _DEFAULT_OUT_PATH = AL.get_env('DEFAULT_OUT_PATH')
    _WIDTH = 600
    _HEIGHT = 400

    def __init__(self, x: int, y: int, on_view_closed: Command, on_accepted: Command):
        super().__init__()
        self.on_view_closed = on_view_closed
        self.setGeometry(x - self._WIDTH // 2, y -
                         self._HEIGHT // 2, self._WIDTH, self._HEIGHT)

        self.layout = QVBoxLayout(self)

        options_box = QWidget()
        grid_layout = QGridLayout(options_box)

        self.layout.addWidget(options_box)

        self.inputs = [QLineEdit() for _ in range(2)]
        labels = [QLabel(x) for x in ['url', 'name']]

        for i, (lab, inp) in enumerate(zip(labels, self.inputs)):
            grid_layout.addWidget(lab, i+1, 1)
            grid_layout.addWidget(inp, i+1, 2)

        path_btn = QPushButton('Select Path')

        self.cur_path_label = ScrollableLabel(
            self, 200, 20, self._DEFAULT_OUT_PATH)
        self.cur_path_label.setAlignment(Qt.AlignLeft)

        grid_layout.addWidget(QLabel('path'), len(labels) + 1, 1)
        grid_layout.addWidget(self.cur_path_label, len(labels)+1, 2)
        grid_layout.addWidget(path_btn, len(labels) + 2, 1)

        self.url_input, self.name_input = self.inputs

        path_btn.clicked.connect(self._open_file_explorer)

        btn_box = QWidget()
        self.layout.addWidget(btn_box)

        inner_layout = QHBoxLayout(btn_box)

        self.add_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")

        self.add_btn.clicked.connect(lambda: on_accepted.execute())
        self.cancel_btn.clicked.connect(lambda: self.close())

        for btn in [self.add_btn, self.cancel_btn]:
            inner_layout.addWidget(btn)

    def _open_file_explorer(self):
        dlg = QFileDialog(directory=self._DEFAULT_OUT_PATH)
        dlg.setFileMode(QFileDialog.Directory)
        dlg.setOption(QFileDialog.ShowDirsOnly)
        if dlg.exec():
            idk = dlg.selectedFiles()
            if len(idk) > 1:
                print('Only one file is required')
            else:
                self.cur_path_label.setText(idk[0])

    def get_url(self) -> str:
        return self.url_input.text()

    def get_name(self) -> str:
        return self.name_input.text()

    def get_path(self) -> str:
        return self.cur_path_label.text()

    def closeEvent(self, a0):
        self.on_view_closed.execute()
        return super().closeEvent(a0)
