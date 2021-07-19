from abc import ABC, abstractmethod
from typing import Iterable
from backend.model.db_models import Playlist


class PlaylistModifiedObserver(ABC):
    @abstractmethod
    def playlist_added(self, playlist: Playlist):
        pass

    @abstractmethod
    def playlist_links_added(self, playlist: Playlist):
        pass
