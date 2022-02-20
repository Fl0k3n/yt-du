from abc import ABC, abstractmethod
from backend.model.db_models import DB_PlaylistLink


class LinkCreatedObserver(ABC):
    @abstractmethod
    def on_link_created(self, playlist_link: DB_PlaylistLink, playlist_rdy: bool):
        pass
