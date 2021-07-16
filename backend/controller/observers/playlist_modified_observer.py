from abc import ABC, abstractmethod
from backend.model.db_models import Playlist


class PlaylistModifiedObserver(ABC):
    @abstractmethod
    def playlist_added(self, playlist: Playlist):
        pass
