from abc import ABC, abstractmethod
from backend.model.db_models import DataLink, PlaylistLink


class PlaylistDlManager(ABC):
    @abstractmethod
    def on_dl_started(self, playlist_link: PlaylistLink, data_link: DataLink):
        pass

    @abstractmethod
    def can_proceed_dl(self, playlist_link: PlaylistLink, data_link: DataLink) -> bool:
        pass

    @abstractmethod
    def on_dl_progress(self, playlist_link: PlaylistLink,
                       data_link: DataLink, bytes_fetched: int):
        pass
