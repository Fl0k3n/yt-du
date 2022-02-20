
from typing import Iterable, List
from backend.db.playlist_repo import PlaylistRepo
from backend.model.playlist import Playlist
from backend.model.playlist_link import PlaylistLink
from backend.utils.observable_list import ObservableList


class Account:
    def __init__(self, repo: PlaylistRepo):
        self.repo = repo
        self.playlists: List[Playlist] = ObservableList(
            self.repo.get_playlists())

    def add_playlist(self, playlist: Playlist):
        self.playlists.append(playlist)

    def get_playlist(self, url: str) -> Playlist:
        # TODO optimize it
        return self.playlists.find(predicate=lambda playlist: playlist.get_url() == url)

    def get_playlists(self) -> Iterable[Playlist]:
        return list(self.playlists)

    def get_playlist_by_id(self, id: int) -> Playlist:
        return self.playlists.find(predicate=lambda playlist: playlist.get_playlist_id() == id)

    def delete_playlist(self, playlist: Playlist):
        playlist.set_deleted()
        self.playlists.remove(playlist)
