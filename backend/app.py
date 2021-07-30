from backend.controller.link_renewer import LinkRenewer
from backend.controller.speedo import Speedo
import sys
from typing import List
from PyQt5.QtWidgets import QApplication
from backend.controller.db_handler import DBHandler
from backend.controller.playlist_manager import PlaylistManager
from backend.controller.gui.main_window_ctl import MainWindowController
from backend.subproc.ipc.ipc_manager import IPCManager


class App(QApplication):
    def __init__(self, argv: List[str], sql_debug: bool = True):
        super().__init__(argv)
        self.db = DBHandler(verbose=sql_debug)
        self.ipc_manager = IPCManager()
        self.speedo = Speedo()
        self.link_renewer = LinkRenewer(self.ipc_manager, self.db)

        self.db.connect()
        self.playlist_manager = PlaylistManager(
            self.db, self.ipc_manager, self.speedo, self.link_renewer)

        self.ipc_manager.add_link_fetched_observer(self.link_renewer)

        self.main_window = MainWindowController(self.playlist_manager, self.db)
        self.main_window.add_app_closed_observer(self.ipc_manager)
        self.main_window.add_app_closed_observer(self.speedo)
        self.main_window.add_app_closed_observer(self.playlist_manager)

    def run(self):
        self.main_window.show()

    def stop(self):
        sys.exit(self.exec())


def main():
    app = App(sys.argv, sql_debug=False)
    app.run()
    app.stop()


if __name__ == '__main__':
    main()
