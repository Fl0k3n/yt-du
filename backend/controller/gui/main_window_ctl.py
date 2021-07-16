from backend.controller.gui.new_playlist_ctl import NewPlaylistController
import PyQt5
from backend.utils.commands.command import CallRcvrCommand
from backend.controller.playlist_manager import PlaylistManager
from backend.controller.db_handler import DBHandler
from backend.view.main_window import MainWindow


class MainWindowController:
    def __init__(self, playlist_manager: PlaylistManager, db: DBHandler):
        self.playlist_mgr = playlist_manager
        self.db = db
        self.new_playlist_ctl = None

        self.playlist_m_observers = [self.playlist_mgr]

        self.view = MainWindow(CallRcvrCommand(
            lambda: self._open_new_playlist_window()))

    def show(self):
        self.view.show()

    def _open_new_playlist_window(self):
        self.new_playlist_ctl = NewPlaylistController(
            self.playlist_mgr, CallRcvrCommand(lambda: self.view.setDisabled(False)))
        self.view.setDisabled(True)
        self.new_playlist_ctl.show()
