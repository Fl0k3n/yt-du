from backend.utils.commands.command import Command
from PyQt5.QtWidgets import QFrame, QPushButton, QVBoxLayout


class OptionsBox(QFrame):
    def __init__(self, playlist_added_cmd: Command):
        super().__init__()

        self.layout = QVBoxLayout(self)

        self.add_playlist_btn = QPushButton("Download")
        self.layout.addWidget(self.add_playlist_btn)

        self.add_playlist_btn.clicked.connect(
            lambda: playlist_added_cmd.execute())
