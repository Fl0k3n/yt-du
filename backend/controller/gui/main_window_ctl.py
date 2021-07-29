from backend.controller.gui.view_changed_observer import ViewChangedObserver
from backend.controller.gui.app_closed_observer import AppClosedObserver
from typing import List
from backend.view.data_summary_box import DataSummaryBox
from backend.controller.gui.new_playlist_ctl import NewPlaylistController
from backend.utils.commands.command import CallRcvrCommand
from backend.controller.playlist_manager import PlaylistManager
from backend.controller.db_handler import DBHandler
from backend.view.main_window import MainWindow
from backend.controller.gui.data_summary_ctl import DataSummaryController
from backend.controller.gui.view_changer import DataViewChanger


class MainWindowController(DataViewChanger):
    def __init__(self, playlist_manager: PlaylistManager, db: DBHandler):
        self.playlist_mgr = playlist_manager
        self.db = db
        self.new_playlist_ctl = None

        self.data_summary_ctl = DataSummaryController(self, self.playlist_mgr)
        self.playlist_mgr.add_pl_modified_observer(self.data_summary_ctl)
        self.data_view = self.data_summary_ctl.get_data_list_view()

        self.view = MainWindow(self.data_view, self, CallRcvrCommand(
            self._open_new_playlist_window), CallRcvrCommand(self._on_window_closed))

        self.view_stack = [self.data_view]

        self.data_view_changed_observers: List[ViewChangedObserver] = [
            self.data_summary_ctl]
        self.app_closed_observers: List[AppClosedObserver] = [
            self.db]

    def add_app_closed_observer(self, obs: AppClosedObserver):
        self.app_closed_observers.append(obs)

    def show(self):
        self.view.show()

    def _open_new_playlist_window(self):
        self.new_playlist_ctl = NewPlaylistController(
            self.playlist_mgr, CallRcvrCommand(lambda: self.view.setDisabled(False)))
        self.view.setDisabled(True)
        self.new_playlist_ctl.show()

    def change_data_view(self, new_view: DataSummaryBox):
        self.view_stack.append(new_view)
        self._change_data_view(new_view)

    def _change_data_view(self, new_view: DataSummaryBox):
        self.data_view = new_view
        self.view.set_data_list(new_view)

    def change_back(self):
        if len(self.view_stack) == 1:
            return

        self.view_stack.pop()
        self._change_data_view(self.view_stack[-1])

        for obs in self.data_view_changed_observers:
            obs.on_changed_back()

    def change_forward(self):
        # TODO
        pass

    def _on_window_closed(self):
        for obs in self.app_closed_observers:
            obs.on_app_closed()
