from backend.controller.playlists_summary_ctl import PlaylistsSummaryController
from backend.controller.view_changed_observer import ViewChangedObserver
from backend.controller.app_closed_observer import AppClosedObserver
from typing import List
from backend.db.playlist_repo import PlaylistRepo
from backend.model.account import Account
from backend.model.playlist_links_fetcher import PlaylistLinksFetcher
from backend.view.data_summary_box import DataSummaryBox
from backend.controller.new_playlist_ctl import NewPlaylistController
from backend.utils.commands.command import CallRcvrCommand
from backend.view.main_window import MainWindow
from backend.controller.view_changer import DataViewChanger


class MainWindowController(DataViewChanger):
    def __init__(self, repo: PlaylistRepo, account: Account,
                 playlist_fetcher: PlaylistLinksFetcher):
        self.repo = repo
        self.account = account
        self.playlist_fetcher = playlist_fetcher
        self.new_playlist_ctl = None

        self.data_view_changed_observers: List[ViewChangedObserver] = []
        self.app_closed_observers: List[AppClosedObserver] = []

    def add_app_closed_observer(self, obs: AppClosedObserver):
        self.app_closed_observers.append(obs)

    def add_view_changed_observer(self, obs: ViewChangedObserver):
        self.data_view_changed_observers.append(obs)

    def show(self, data_view: DataSummaryBox):
        self.data_view = data_view

        self.view = MainWindow(self.data_view, self, CallRcvrCommand(
            self._open_new_playlist_window), CallRcvrCommand(self._on_window_closed))

        self.view_stack = [self.data_view]
        self.view.show()

    def _open_new_playlist_window(self):
        self.new_playlist_ctl = NewPlaylistController(
            self.account, self.repo, self.playlist_fetcher,
            CallRcvrCommand(lambda: self.view.setDisabled(False)))

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

    def view_deleted(self, view: DataSummaryBox):
        # nothing todo as long as change forward doesnt work
        pass
