
from datetime import datetime
from backend.model.data_status import DataStatus
from backend.model.db_models import DB_Playlist
from backend.model.downloadable import Downloadable
from backend.model.playlist_link import PlaylistLink
from backend.utils.property import Property


class Playlist(Downloadable):
    def __init__(self, db_playlist: DB_Playlist) -> None:
        self.db_playlist = db_playlist
        self.playlist_links = [PlaylistLink(
            db_link) for db_link in self.db_playlist.links]
        self._setup_properties()

    def _setup_properties(self):
        self.playlist_id_property = Property(self.db_playlist.playlist_id)
        self.name_property = Property(self.db_playlist.name)
        self.url_property = Property(self.db_playlist.url)
        self.directory_path_property = Property(
            self.db_playlist.directory_path)
        self.added_at_property = Property(self.db_playlist.added_at)
        self.finished_at_property = Property(self.db_playlist.finished_at)
        self.status_property = Property(DataStatus(self.db_playlist.status))

    def get_playlist_id(self) -> int:
        return self.playlist_id_property.get()

    def get_name(self) -> str:
        return self.name_property.get()

    def get_url(self) -> str:
        return self.url_property.get()

    def get_path(self) -> str:
        # TODO path
        return self.directory_path_property.get()

    def get_added_at(self) -> datetime:
        return self.added_at_property.get()

    def get_finished_at(self) -> datetime:
        return self.finished_at_property.get()

    def get_status(self) -> DataStatus:
        return self.status_property.get()

    def set_name(self, name: str):
        self.db_playlist.name = name
        self.name_property.set(name)

    def set_url(self, url: str):
        self.db_playlist.url = url
        self.url_property.set(url)

    def set_directory_path(self, path: str):
        self.db_playlist.directory_path = path
        self.directory_path_property.set(path)

    def set_added_at(self, timestamp: datetime):
        self.db_playlist.added_at = timestamp
        self.added_at_property.set(timestamp)

    def set_finished_at(self, timestamp: datetime):
        self.db_playlist.finished_at = timestamp
        self.finished_at_property.set(timestamp)

    def get_downloaded_bytes(self) -> int:
        return sum(link.get_downloaded_bytes() for link in self.playlist_links)

    def get_size_bytes(self) -> int:
        return sum(link.get_size_bytes() for link in self.playlist_links)

    def set_status(self, status: DataStatus):
        self.status_property.set(status)

    def __hash__(self):
        return hash(self.db_playlist.playlist_id)

    def __eq__(self, other):
        if type(self) == type(other):
            return self.db_playlist.playlist_id == other.db_playlist.playlist_id
        return False
