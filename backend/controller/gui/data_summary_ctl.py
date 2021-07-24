from backend.controller.gui.view_changed_observer import ViewChangedObserver
from backend.controller.observers.playlist_modified_observer import PlaylistModifiedObserver
from backend.model.displayable import Displayable
from typing import Dict, Iterable, List
from collections import deque
from backend.view.data_list_item import DataListItem
from backend.model.db_models import Playlist, PlaylistLink
from controller.playlist_manager import PlaylistManager
from view.data_summary_box import DataSummaryBox
from utils.commands.command import CallRcvrCommand, Command
from controller.gui.view_changer import DataViewChanger


class DataSummaryController(PlaylistModifiedObserver, ViewChangedObserver):
    _MAX_VISIBLE = 7
    _BOX_WIDTH, _BOX_HEIGHT = 600, 600

    def __init__(self, view_changer: DataViewChanger, playlist_manager: PlaylistManager):
        self.playlist_mgr = playlist_manager
        self.playlist_view = DataSummaryBox(self._BOX_WIDTH, self._BOX_HEIGHT)
        self.view = self.playlist_view
        self.view_changer = view_changer

        self.displayed_playlist = None

        self.item_count = self.playlist_mgr.get_item_count()
        self.view.set_scrollable_size(DataListItem.HEIGHT * self.item_count)

        self.playlists = self.playlist_mgr.get_playlists(
            limit=self._MAX_VISIBLE)

        self.visible_playlists: List[DataListItem] = []
        self.displayable_to_view: Dict[Displayable, DataListItem] = {}

        pl_cmds = [self._get_playlist_details_cmd(playlist)
                   for playlist in self.playlists]

        self.visible_playlists = self._create_view_items(
            self.playlists, pl_cmds)
        self.visible_items = self.visible_playlists

        self.view.show_all(self.visible_items)

        # tuples (playlist, visible_items) for views
        # that should correspond to main_window_ctl view stack
        self.displayed_items_stack = [
            (self.displayed_playlist, self.visible_items)]

    def _show_playlist_details(self, playlist: Playlist):
        self.view = DataSummaryBox(self._BOX_WIDTH, self._BOX_HEIGHT)
        self.view.set_scrollable_size(
            DataListItem.HEIGHT * len(playlist.links))

        link_cmds = [self._get_link_details_cmd(
            link) for link in playlist.links]

        self.visible_items = self._create_view_items(playlist.links, link_cmds)
        self.view.show_all(self.visible_items)
        self.view_changer.change_data_view(self.view)

        self.displayed_playlist = playlist
        self.displayed_items_stack.append(
            (self.displayed_playlist, self.visible_items))

    def playlist_added(self, playlist: Playlist):
        self.playlists = [playlist, *self.visible_playlists]  # TODO
        dl_item = playlist.to_data_list_item(
            self._get_playlist_details_cmd(playlist))

        self.displayable_to_view[playlist] = dl_item

        self._update_status(playlist)

        self.visible_playlists = [dl_item, *self.visible_playlists]
        self.playlist_view.append_top(dl_item)

    def playlist_links_added(self, playlist: Playlist):
        if self.displayed_playlist == playlist:
            self.view_changer.change_back()
            self._update_status(playlist)
            self._show_playlist_details(playlist)

    def playlist_dl_started(self, playlist: Playlist):
        self._update_status(playlist)
        for el in playlist.links:
            self._update_status(el)

    def _update_status(self, item: Displayable):
        if item in self.displayable_to_view:
            self.displayable_to_view[item].set_status(str(item.get_status()))

    def _update_dl_progress(self, item: Displayable,
                            total_size: int, current_dl: int):
        if item in self.displayable_to_view:
            self.displayable_to_view[item].update_progress_bar(
                current_dl / total_size)

    def get_data_list_view(self) -> DataSummaryBox:
        return self.view

    def _create_view_items(self, items: Iterable[Displayable],
                           show_details_commands: Iterable[Command]) -> Iterable[DataListItem]:
        res = []
        for item, command in zip(items, show_details_commands):
            if item in self.displayable_to_view:
                res.append(self.displayable_to_view[item])
            else:
                view_item = item.to_data_list_item(command)
                res.append(view_item)
                self.displayable_to_view[item] = view_item
                try:
                    view_item.update_progress_bar(
                        item.get_downloaded_bytes() / item.get_size_bytes())
                except ZeroDivisionError:
                    view_item.update_progress_bar(0)
        return res

    def _get_playlist_details_cmd(self, playlist: Playlist) -> Command:
        return CallRcvrCommand(self._show_playlist_details, playlist)

    def _get_link_details_cmd(self, link: PlaylistLink) -> Command:
        return CallRcvrCommand(lambda: print("HALO"))  # TODO show errs

    def on_changed_back(self):
        self.displayed_playlist, self.visible_items = self.displayed_items_stack.pop()

    def on_changed_forward(self):
        # TODO
        pass

    def _update_pl_progress(self, playlist: Playlist):
        pl_size = self.playlist_mgr.get_playlist_size_bytes(playlist)
        pl_dled = self.playlist_mgr.get_playlist_downloaded_bytes(playlist)
        self._update_dl_progress(playlist, pl_size, pl_dled)

    def _update_link_progress(self, playlist_link: PlaylistLink):
        link_size = self.playlist_mgr.get_link_size_bytes(playlist_link)
        link_dled = self.playlist_mgr.get_link_downloaded_bytes(playlist_link)
        self._update_dl_progress(playlist_link, link_size, link_dled)

    def playlist_dl_progressed(self, playlist: Playlist, playlist_link: PlaylistLink):
        self._update_pl_progress(playlist)
        self._update_link_progress(playlist_link)

    def playlist_link_dled(self, playlist_link: PlaylistLink):
        self._update_status(playlist_link)

    def playlist_link_merging(self, playlist_link: PlaylistLink):
        self._update_status(playlist_link)

    def playlist_link_finished(self, playlist_link: PlaylistLink):
        self._update_status(playlist_link)
