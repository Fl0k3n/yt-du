
from backend.model.db_models import DB_Playlist
from backend.model.downloadable import Downloadable


class Playlist(Downloadable):
    def __init__(self, db_playlist: DB_Playlist) -> None:
        self.db_playlist = db_playlist
