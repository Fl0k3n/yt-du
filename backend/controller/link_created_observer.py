from abc import ABC, abstractmethod
from backend.model.db_models import PlaylistLink


class LinkCreatedObserver(ABC):
    @abstractmethod
    def on_link_created(self, playlist_link: PlaylistLink, playlist_rdy:bool):
        pass
