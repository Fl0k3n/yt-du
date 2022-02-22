from typing import Iterable
from backend.model.link_creator import LinkCreator
from backend.model.playlist import Playlist
from backend.model.playlist_fetched_observer import PlaylistFetchedObserver
from backend.db.playlist_repo import PlaylistRepo
from backend.model.account import Account
from backend.model.data_status import DataStatus
from backend.subproc.ipc.ipc_manager import IPCManager


class PlaylistLinksFetcher(PlaylistFetchedObserver):

    def __init__(self, account: Account, repo: PlaylistRepo, link_creator: LinkCreator, ipc_mgr: IPCManager):
        self.account = account
        self.repo = repo
        self.link_creator = link_creator
        self.ipc_mgr = ipc_mgr

    def fetch_playlist_links(self, playlist: Playlist):
        playlist.set_status(DataStatus.WAIT_FOR_FETCH)
        self.repo.update()

        self.ipc_mgr.query_playlist_links(playlist)
        self.account.add_playlist(playlist)

    def on_playlist_fetched(self, playlist_id: int,
                            playlist_idxs: Iterable[int],
                            links: Iterable[str],
                            titles: Iterable[str],
                            data_links: Iterable[Iterable[str]]):
        playlist = self.account.get_playlist_by_id(playlist_id)

        if playlist is None:
            return

        playlist.set_status(DataStatus.WAIT_FOR_DL)

        pl_links = []
        for idx, link, title in zip(playlist_idxs, links, titles):
            path = playlist.create_video_path(title, idx)
            pl_link = self.repo.create_playlist_link(
                playlist, idx, title, link, path)
            pl_link.set_status(DataStatus.WAIT_FOR_DL)
            pl_links.append(pl_link)

        # this may be time consuming, so it is done in a separate thread, callback is called in the GUI thread
        for pl_link, dlinks in zip(pl_links, data_links):
            self.link_creator.schedule_creation_task(pl_link, dlinks)
