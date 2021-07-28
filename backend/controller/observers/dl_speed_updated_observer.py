from abc import ABC, abstractmethod
from backend.model.db_models import Playlist


class DlSpeedUpdatedObserver(ABC):
    @abstractmethod
    def playlist_speed_updated(self, playlist: Playlist, speed_MBps: float):
        pass
