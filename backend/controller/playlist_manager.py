from typing import List
from backend.controller.db_handler import DBHandler
from backend.model.db_models import Playlist
from backend.controller.observers.playlist_modified_observer import PlaylistModifiedObserver


class PlaylistManager(PlaylistModifiedObserver):
    def __init__(self, db: DBHandler):
        self.db = db
        self.loaded_playlists = []  # list of loaded playlists
        self.pl_map = {}  # playlist_url -> idx in list above

    def playlist_added(self, playlist: Playlist):
        print('playlist added')

    def add_playlist(self, playlist: Playlist):
        self.db.add_playlist(playlist)
        print('added')

    def get_playlist(self, url: str) -> Playlist:
        stored = self._get_stored_playlist(url) if url in self.pl_map else \
            self.db.get_playlist(url=url)

        return stored

    def get_playlists(self, offset: int = 0, limit: int = None) -> List[Playlist]:
        # check if was cached
        playlists = self.db.get_playlists(offset, limit)
        # cache them
        return playlists

    def _get_stored_playlist(self, url: str) -> Playlist:
        return self.loaded_playlists[self.pl_map[url]]

    def get_item_count(self) -> int:
        return self.db.get_playlist_count()  # + get_link_count?
