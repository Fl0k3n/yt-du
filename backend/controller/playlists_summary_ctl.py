import logging
from collections import deque
from typing import Deque, Dict, List
from backend.controller.data_list_items_factory import DataListItemsFactory
from backend.controller.view_changed_observer import ViewChangedObserver
from backend.controller.view_changer import DataViewChanger
from backend.model.account import Account
from backend.model.playlist import Playlist
from backend.model.playlist_dl_supervisor import PlaylistDownloadSupervisor
from backend.model.playlist_link import PlaylistLink
from backend.utils.commands.command import CallRcvrCommand
from backend.view.data_list_item import DataListItem
from backend.view.data_summary_box import DataSummaryBox
from backend.view.link_list_item import LinkListItem
from backend.view.playlist_list_item import PlaylistListItem


class ViewStackItem:
    def __init__(self, playlist: Playlist, view: DataSummaryBox, view_items: List[DataListItem]) -> None:
        self.playlist = playlist
        self.view = view
        self.view_items = view_items


class PlaylistsSummaryController(ViewChangedObserver):
    _BOX_WIDTH, _BOX_HEIGHT = 850, 700
    _DELETE_PL_MENU_NAME = 'Delete Entry'

    def __init__(self, account: Account,
                 view_changer: DataViewChanger,
                 list_items_factory: DataListItemsFactory,
                 playlist_dl_supervisor: PlaylistDownloadSupervisor):
        self.account = account
        self.view_changer = view_changer
        self.list_items_factory = list_items_factory
        self.playlist_dl_supervisor = playlist_dl_supervisor
        self.view_changer = view_changer

        self._init_view()

    def _init_view(self):
        self.playlists_view = DataSummaryBox(self._BOX_WIDTH, self._BOX_HEIGHT)

        self.playlists_view.set_scrollable_size(
            DataListItem.HEIGHT * self.account.get_item_count())

        self.playlists_observable = self.account.get_playlists_observable_list()

        self.visible_playlists: Deque[PlaylistListItem] = deque()
        self.playlist_to_list_item: Dict[Playlist, PlaylistListItem] = {}

        for playlist in reversed(self.playlists_observable):
            self._add_playlist(playlist)

        self.account \
            .get_playlists_observable_list() \
            .add_on_changed_observer(on_added_cb=self._add_playlist,
                                     on_removed_cb=self._on_playlist_deleted)

        self.displayed_items_stack: List[ViewStackItem] = [
            ViewStackItem(None, self.playlists_view, self.visible_playlists)]

        self.playlists_view.show_all(self.visible_playlists)

    def _add_playlist(self, playlist: Playlist):
        list_item = self.list_items_factory.create_data_list_item(playlist)

        list_item.add_show_details_command(CallRcvrCommand(
            self._show_playlist_details, playlist))

        list_item.add_pause_command(CallRcvrCommand(
            self.playlist_dl_supervisor.on_playlist_pause_requested, playlist))

        list_item.add_resume_command(CallRcvrCommand(
            self.playlist_dl_supervisor.on_playlist_resume_requested, playlist))

        list_item.add_menu_item(self._DELETE_PL_MENU_NAME, CallRcvrCommand(
            self.account.delete_playlist, playlist))

        playlist \
            .get_playlist_links_obervable_list() \
            .add_on_changed_observer(on_added_cb=self._on_playlist_link_added)

        self.visible_playlists.appendleft(list_item)
        self.playlists_view.append_top(list_item)
        self.playlist_to_list_item[playlist] = list_item

    def _on_playlist_link_added(self, playlist_link: PlaylistLink):
        stack_top = self.displayed_items_stack[-1]
        visible_playlist = stack_top.playlist

        if visible_playlist is not None and playlist_link.get_playlist() == visible_playlist:
            new_link = self._add_link(playlist_link)
            stack_top.view_items.append(new_link)
            stack_top.view.append(new_link)

    def _on_playlist_deleted(self, playlist: Playlist):
        playlist_view = self.playlist_to_list_item.pop(playlist)
        self.visible_playlists.remove(playlist_view)
        self.playlists_view.delete_item(playlist_view)

    def _add_link(self, playlist_link: PlaylistLink) -> LinkListItem:
        list_item = self.list_items_factory.create_data_list_item(
            playlist_link)

        list_item.add_show_details_command(
            CallRcvrCommand(lambda: logging.info("link details requested, no action implemented")))

        list_item.add_pause_command(CallRcvrCommand(
            self.playlist_dl_supervisor.on_link_pause_requested, playlist_link))

        list_item.add_resume_command(CallRcvrCommand(
            self.playlist_dl_supervisor.on_link_resume_requested, playlist_link))

        return list_item

    def _show_playlist_details(self, playlist: Playlist):
        view = DataSummaryBox(self._BOX_WIDTH, self._BOX_HEIGHT)

        links = playlist.get_playlist_links()
        view.set_scrollable_size(DataListItem.HEIGHT * len(links))

        visible_items = [self._add_link(link) for link in links]

        self.displayed_items_stack.append(
            ViewStackItem(playlist, view, visible_items))

        view.show_all(visible_items)
        self.view_changer.change_data_view(view)

    def on_changed_back(self):
        cur_view = self.displayed_items_stack.pop()

        for item in cur_view.view_items:
            item.unbind_properties()

    def on_changed_forward(self):
        # TODO
        pass

    def get_data_summary_view(self) -> DataSummaryBox:
        return self.displayed_items_stack[-1].view
