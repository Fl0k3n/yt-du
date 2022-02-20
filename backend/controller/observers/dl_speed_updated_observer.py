from abc import ABC, abstractmethod
from backend.model.playlist import Playlist


class DlSpeedUpdatedObserver(ABC):
    @abstractmethod
    def playlist_speed_updated(self, playlist: Playlist, speed_MBps: float):
        pass
