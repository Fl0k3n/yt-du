
from typing import Iterable
from backend.db.playlist_repo import PlaylistRepo
from backend.model.playlist import Playlist
from backend.utils.observable_list import ObservableList


class Account:
    def __init__(self, repo: PlaylistRepo):
        self.repo = repo
        self.playlists = ObservableList[Playlist](
            self.repo.get_playlists())

    def add_playlist(self, playlist: Playlist):
        self.playlists.append(playlist)

    def get_playlist(self, url: str) -> Playlist:
        # TODO optimize it
        return self.playlists.find(predicate=lambda playlist: playlist.get_url() == url)

    def get_playlists(self) -> Iterable[Playlist]:
        return list(self.playlists)

    def get_playlists_observable_list(self) -> ObservableList[Playlist]:
        return self.playlists

    def get_item_count(self) -> int:
        return len(self.playlists)

    def get_playlist_by_id(self, id: int) -> Playlist:
        return self.playlists.find(predicate=lambda playlist: playlist.get_playlist_id() == id)

    def delete_playlist(self, playlist: Playlist):
        self.playlists.remove(playlist)
        self.repo.delete_playlist(playlist)
