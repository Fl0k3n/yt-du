from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton
from backend.utils.commands.command import Command


class YesNoDialog(QDialog):
    def __init__(self, msg, yes_command: Command, no_command: Command,
                 yes_msg: str = 'Yes', no_msg: str = 'No', close_on_click: bool = True):
        super().__init__()
        self.label = QLabel(msg)

        layout = QGridLayout(self)
        layout.addWidget(self.label, 1, 1, 1, 2)

        def wrapper(cmd):
            if close_on_click:
                self.close()
            cmd.execute()

        cmds = [(lambda y: lambda: wrapper(y))(x)
                for x in [yes_command, no_command]]

        msgs = [yes_msg, no_msg]

        for i, (msg, cmd) in enumerate(zip(msgs, cmds)):
            btn = QPushButton(msg)
            btn.clicked.connect((lambda x: lambda: x())(cmd))
            layout.addWidget(btn, 2, i+1)
