from backend.db.playlist_repo import PlaylistRepo
from backend.model.account import Account
from backend.model.data_status import DataStatus
from backend.model.playlist import Playlist
from backend.model.playlist_link import PlaylistLink
from backend.subproc.ipc.ipc_manager import IPCManager


class PlaylistsController:
    def __init__(self, account: Account, repo: PlaylistRepo, ipc_mgr: IPCManager) -> None:
        self.account = account
        self.repo = repo
        self.ipc_mgr = ipc_mgr

    def on_playlist_added(self, playlist: Playlist):
        playlist.set_status(DataStatus.WAIT_FOR_FETCH)
        self.ipc_mgr.query_playlist_links(playlist)

    def delete_playlist(self, playlist: Playlist):
        self.account.delete_playlist(playlist)
