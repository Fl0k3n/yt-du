from backend.controller.observers.playlist_modified_observer import PlaylistModifiedObserver
from backend.model.displayable import Displayable
from typing import Iterable
from collections import deque
from backend.view.data_list_item import DataListItem
from backend.model.db_models import Playlist
from controller.playlist_manager import PlaylistManager
from view.data_summary_box import DataSummaryBox
from utils.commands.command import CallRcvrCommand, Command
from controller.gui.view_changer import DataViewChanger


class DataSummaryController(PlaylistModifiedObserver):
    _MAX_VISIBLE = 7
    _BOX_WIDTH, _BOX_HEIGHT = 600, 600

    def __init__(self, view_changer: DataViewChanger, playlist_manager: PlaylistManager):
        self.playlist_mgr = playlist_manager
        self.playlist_view = DataSummaryBox(self._BOX_WIDTH, self._BOX_HEIGHT)
        self.view = self.playlist_view
        self.view_changer = view_changer

        self.item_count = self.playlist_mgr.get_item_count()
        self.view.set_scrollable_size(DataListItem.HEIGHT * self.item_count)

        self.playlists = self.playlist_mgr.get_playlists(
            limit=self._MAX_VISIBLE)

        self.visible_playlists = []
        self.visible_items = self.visible_playlists

        pl_cmds = [self._get_playlist_details_cmd(playlist)
                   for playlist in self.playlists]

        self.visible_items = self._create_view_items(self.playlists, pl_cmds)
        self.view.show_all(self.visible_items)

    def _show_playlist_details(self, playlist: Playlist):
        self.view = DataSummaryBox(self._BOX_WIDTH, self._BOX_HEIGHT)
        self.view.set_scrollable_size(
            DataListItem.HEIGHT * len(playlist.links))

        link_cmds = [CallRcvrCommand(
            lambda: print("HALO")) for link in playlist.links]

        self.visible_items = self._create_view_items(playlist.links, link_cmds)
        self.view.show_all(self.visible_items)
        self.view_changer.change_data_view(self.view)

    def playlist_added(self, playlist: Playlist):
        self.playlists = [playlist, *self.visible_playlists]  # TODO
        dl_item = playlist.to_data_list_item(
            self._get_playlist_details_cmd(playlist))

        self.visible_playlists = [dl_item, *self.visible_playlists]
        self.playlist_view.append_top(dl_item)

    def get_data_list_view(self) -> DataSummaryBox:
        return self.view

    def _create_view_items(self, items: Iterable[Displayable],
                           show_details_commands: Iterable[Command]) -> Iterable[DataListItem]:
        return [item.to_data_list_item(command) for item, command in zip(items, show_details_commands)]

    def _get_playlist_details_cmd(self, playlist) -> Command:
        return CallRcvrCommand(self._show_playlist_details, playlist)
