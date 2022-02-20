from backend.controller.gui.app_closed_observer import AppClosedObserver
from backend.controller.observers.dl_speed_updated_observer import DlSpeedUpdatedObserver
from backend.controller.gui.view_changed_observer import ViewChangedObserver
from backend.controller.observers.playlist_modified_observer import PlaylistModifiedObserver
from backend.model.downloadable import Downloadable
from typing import Dict, Iterable, List, Set
from collections import deque
from backend.view.data_list_item import DataListItem
from backend.model.db_models import DB_Playlist, DB_PlaylistLink
from backend.controller.playlist_manager import PlaylistManager
from backend.view.data_summary_box import DataSummaryBox
from utils.commands.command import CallRcvrCommand, Command
from backend.controller.gui.view_changer import DataViewChanger


class DataSummaryController(PlaylistModifiedObserver, ViewChangedObserver):
    _MAX_VISIBLE = 999999  # TODO
    _BOX_WIDTH, _BOX_HEIGHT = 700, 600
    _DELETE_PL_MENU_NAME = 'Delete Entry'

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
        self.displayable_to_view: Dict[Downloadable, DataListItem] = {}

        self.displayable_to_summary_box: Dict[Downloadable, DataSummaryBox] = {
        }

        self._init_playlist_view()

        # tuples (playlist, visible_items) for views
        # that should correspond to main_window_ctl view stack
        self.displayed_items_stack = [
            (self.displayed_playlist, self.visible_items)]

    def _init_playlist_view(self):
        show_details_cmds = [self._get_playlist_details_cmd(playlist)
                             for playlist in self.playlists]

        pause_cmds = [self._get_playlist_pause_cmd(playlist)
                      for playlist in self.playlists]

        resume_cmds = [self._get_playlist_resume_cmd(playlist)
                       for playlist in self.playlists]

        are_pausable = [self.playlist_mgr.is_playlist_pausable(
            playlist) for playlist in self.playlists]

        are_resumable = [self.playlist_mgr.is_playlist_resumable(
            playlist) for playlist in self.playlists]

        self.visible_playlists = self._create_view_items(
            self.playlists, show_details_cmds, pause_cmds,
            resume_cmds, are_pausable, are_resumable)

        for pl, view in zip(self.playlists, self.visible_playlists):
            if self.playlist_mgr.is_playlist_removable(pl):
                view.add_menu_item(
                    self._DELETE_PL_MENU_NAME,
                    self._get_playlist_delete_cmd(pl))

        self.visible_items = self.visible_playlists

        self.view.show_all(self.visible_items)

    def _show_playlist_details(self, playlist: DB_Playlist):
        self.view = DataSummaryBox(self._BOX_WIDTH, self._BOX_HEIGHT)
        self.displayable_to_summary_box[playlist] = self.view
        self.view.set_scrollable_size(
            DataListItem.HEIGHT * len(playlist.links))

        show_details_cmds = [self._get_link_details_cmd(
            link) for link in playlist.links]

        pause_cmds = [self._get_link_pause_cmd(
            link) for link in playlist.links]

        resume_cmds = [self._get_link_resume_cmd(link)
                       for link in playlist.links]

        are_pausable = [self.playlist_mgr.is_link_pausable(
            link) for link in playlist.links]

        are_resumable = [self.playlist_mgr.is_link_resumable(
            link) for link in playlist.links]

        self.visible_items = self._create_view_items(
            playlist.links, show_details_cmds, pause_cmds, resume_cmds, are_pausable, are_resumable)

        self.view.show_all(self.visible_items)
        self.view_changer.change_data_view(self.view)

        self.displayed_playlist = playlist
        self.displayed_items_stack.append(
            (self.displayed_playlist, self.visible_items))

    def playlist_added(self, playlist: DB_Playlist):
        self.playlists = [playlist, *self.playlists]

        dl_item = playlist.to_data_list_item(
            self._get_playlist_details_cmd(playlist),
            self._get_playlist_pause_cmd(playlist),
            self._get_playlist_resume_cmd(playlist),
            self.playlist_mgr.is_playlist_pausable(playlist),
            self.playlist_mgr.is_playlist_resumable(playlist))

        dl_item.add_menu_item(
            self._DELETE_PL_MENU_NAME,
            self._get_playlist_delete_cmd(playlist))

        self.displayable_to_view[playlist] = dl_item

        self._update_status(playlist)

        self.visible_playlists = [dl_item, *self.visible_playlists]
        self.playlist_view.append_top(dl_item)

    def playlist_links_added(self, playlist: DB_Playlist):
        if self.displayed_playlist == playlist:
            self.view_changer.change_back()
            self._update_status(playlist)
            self._show_playlist_details(playlist)

        self._set_pausable(playlist, True)
        self._set_removable(playlist, True)
        self.displayable_to_view[playlist].set_size(
            playlist.get_formatted_size())

    def playlist_dl_started(self, playlist: DB_Playlist):
        self._update_status(playlist)
        self._set_pausable(playlist, True)
        self._set_removable(playlist, False)

    def link_dl_started(self, playlist_link: DB_PlaylistLink):
        self._update_status(playlist_link)
        self._set_pausable(playlist_link, True)

    def _update_status(self, item: Downloadable):
        if item in self.displayable_to_view:
            self.displayable_to_view[item].set_status(str(item.get_status()))

    def _update_dl_progress(self, item: Downloadable,
                            total_size: int, current_dl: int):
        if item in self.displayable_to_view:
            self.displayable_to_view[item].update_progress_bar(
                current_dl / total_size)

    def get_data_list_view(self) -> DataSummaryBox:
        return self.view

    def _create_view_items(self, items: Iterable[Downloadable],
                           show_details_commands: Iterable[Command],
                           pause_commands: Iterable[Command],
                           resume_commands: Iterable[Command],
                           are_pausable: Iterable[bool],
                           are_resumable: Iterable[bool]) -> Iterable[DataListItem]:
        res = []
        for item, show_details_cmd, pause_cmd, resume_cmd, is_pausable, is_resumable in \
                zip(items, show_details_commands, pause_commands, resume_commands, are_pausable, are_resumable):

            if item in self.displayable_to_view:
                res.append(self.displayable_to_view[item])
            else:
                view_item = item.to_data_list_item(
                    show_details_cmd, pause_cmd, resume_cmd, is_pausable, is_resumable)
                res.append(view_item)
                self.displayable_to_view[item] = view_item
                try:
                    view_item.update_progress_bar(
                        item.get_downloaded_bytes() / item.get_size_bytes())
                except ZeroDivisionError:
                    view_item.update_progress_bar(0)
        return res

    def _get_playlist_details_cmd(self, playlist: DB_Playlist) -> Command:
        return CallRcvrCommand(self._show_playlist_details, playlist)

    def _get_playlist_pause_cmd(self, playlist: DB_Playlist) -> Command:
        return CallRcvrCommand(self.playlist_mgr.on_playlist_pause_requested, playlist)

    def _get_playlist_resume_cmd(self, playlist: DB_Playlist) -> Command:
        return CallRcvrCommand(self.playlist_mgr.on_playlist_resume_requested, playlist)

    def _get_link_details_cmd(self, link: DB_PlaylistLink) -> Command:
        # TODO show errs
        return CallRcvrCommand(lambda: print("LINK DETAILS REQUESTED"))

    def _get_link_pause_cmd(self, link: DB_PlaylistLink) -> Command:
        return CallRcvrCommand(self.playlist_mgr.on_link_pause_requested, link)

    def _get_link_resume_cmd(self, link: DB_PlaylistLink) -> Command:
        return CallRcvrCommand(self.playlist_mgr.on_link_resume_requested, link)

    def _get_playlist_delete_cmd(self, playlist: DB_Playlist) -> Command:
        return CallRcvrCommand(self.playlist_mgr.delete_playlist, playlist)

    def on_changed_back(self):
        self.displayed_playlist, self.visible_items = self.displayed_items_stack.pop()

    def on_changed_forward(self):
        # TODO
        pass

    def _update_pl_progress(self, playlist: DB_Playlist):
        pl_size = self.playlist_mgr.get_playlist_size_bytes(playlist)
        pl_dled = self.playlist_mgr.get_playlist_downloaded_bytes(playlist)
        self._update_dl_progress(playlist, pl_size, pl_dled)

    def _update_link_progress(self, playlist_link: DB_PlaylistLink):
        link_size = self.playlist_mgr.get_link_size_bytes(playlist_link)
        link_dled = self.playlist_mgr.get_link_downloaded_bytes(playlist_link)
        self._update_dl_progress(playlist_link, link_size, link_dled)

    def playlist_dl_progressed(self, playlist: DB_Playlist, playlist_link: DB_PlaylistLink):
        self._update_pl_progress(playlist)
        self._update_link_progress(playlist_link)

    def playlist_link_dled(self, playlist_link: DB_PlaylistLink):
        self._update_status(playlist_link)
        self._set_pausable(playlist_link, False)

    def playlist_link_merging(self, playlist_link: DB_PlaylistLink):
        self._update_status(playlist_link)

    def playlist_link_finished(self, playlist_link: DB_PlaylistLink):
        self._update_status(playlist_link)

    def playlist_finished(self, playlist: DB_Playlist):
        self._update_status(playlist)
        self._set_pausable(playlist, False)
        self._set_removable(playlist, True)

    def playlist_link_resume_requested(self, playlist_link: DB_PlaylistLink):
        self._set_resumable(playlist_link, False)

    def playlist_link_pause_requested(self, playlist_link: DB_PlaylistLink):
        self._set_pausable(playlist_link, False)

    def playlist_pause_requested(self, playlist: DB_Playlist):
        self._set_pausable(playlist, False)

    def playlist_resume_requested(self, playlist: DB_Playlist):
        self._set_resumable(playlist, False)
        self._set_removable(playlist, False)

    def playlist_link_paused(self, playlist_link: DB_PlaylistLink):
        self._update_status(playlist_link)
        self._set_resumable(playlist_link, True)

    def playlist_paused(self, playlist: DB_Playlist):
        self._update_status(playlist)
        self._set_resumable(playlist, True)
        self._set_removable(playlist, True)

    def _set_removable(self, playlist: DB_Playlist, removable: bool):
        try:
            item = self.displayable_to_view[playlist]
            if removable:
                item.add_menu_item(self._DELETE_PL_MENU_NAME,
                                   self._get_playlist_delete_cmd(playlist))
            else:
                item.remove_menu_item(self._DELETE_PL_MENU_NAME)
        except KeyError:
            pass

    def _set_pausable(self, item: Downloadable, pausable: bool):
        try:
            self.displayable_to_view[item].set_pausable(pausable)
        except KeyError:
            pass

    def _set_resumable(self, item: Downloadable, resumable: bool):
        try:
            self.displayable_to_view[item].set_resumable(resumable)
        except KeyError:
            pass

    def playlist_speed_updated(self, playlist: DB_Playlist, speed_MBps: float):
        try:
            self.displayable_to_view[playlist].set_dl_speed(str(speed_MBps))
        except KeyError:
            pass

    def inconsistenty_fixed(self, playlist_link: DB_PlaylistLink):
        playlist = playlist_link.playlist
        self._set_pausable(playlist_link, True)
        self._set_resumable(playlist_link, False)
        self._update_status(playlist_link)
        self._update_status(playlist)
        self._update_link_progress(playlist_link)
        self._update_pl_progress(playlist)

    def playlist_deleted(self, playlist: DB_Playlist):
        self.playlists.remove(playlist)
        view = self.displayable_to_view.pop(playlist)
        self.playlist_view.delete_item(view)
        self.visible_playlists.remove(view)

        for link in playlist.links:
            if link in self.displayable_to_view:
                self.displayable_to_view.pop(link)

        if playlist in self.displayable_to_summary_box:
            box = self.displayable_to_summary_box.pop(playlist)
            self.view_changer.view_deleted(box)
