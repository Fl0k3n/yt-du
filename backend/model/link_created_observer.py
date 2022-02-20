from abc import ABC, abstractmethod
from backend.model.data_link import DataLink

from backend.model.playlist_link import PlaylistLink


class LinkCreatedObserver(ABC):
    @abstractmethod
    def on_link_created(self, playlist_link: PlaylistLink, data_link: DataLink, playlist_rdy: bool):
        pass
