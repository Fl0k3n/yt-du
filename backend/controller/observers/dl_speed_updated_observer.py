from abc import ABC, abstractmethod
from backend.model.db_models import DB_Playlist


class DlSpeedUpdatedObserver(ABC):
    @abstractmethod
    def playlist_speed_updated(self, playlist: DB_Playlist, speed_MBps: float):
        pass
