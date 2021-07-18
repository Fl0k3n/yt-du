import sys
from typing import List
from PyQt5.QtWidgets import QApplication
from controller.db_handler import DBHandler
from controller.playlist_manager import PlaylistManager
from controller.gui.main_window_ctl import MainWindowController
from subproc.ipc.ipc_manager import IPCManager


class App(QApplication):
    def __init__(self, argv: List[str], sql_debug: bool = True):
        super().__init__(argv)
        self.db = DBHandler(verbose=sql_debug)
        self.ipc_manager = IPCManager()
        self.db.connect()
        self.playlist_manager = PlaylistManager(self.db, self.ipc_manager)
        self.main_window = MainWindowController(self.playlist_manager, self.db)

    def run(self):
        self.main_window.show()

    def stop(self):
        sys.exit(self.exec())


def main():
    app = App(sys.argv)
    app.run()
    app.stop()


if __name__ == '__main__':
    main()
