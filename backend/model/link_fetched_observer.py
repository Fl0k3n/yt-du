from abc import ABC, abstractmethod
from typing import Iterable

from backend.model.playlist_link import PlaylistLink


class LinkFetchedObserver(ABC):
    @abstractmethod
    def on_link_fetched(self, original_link: PlaylistLink, data_links: Iterable[str]):
        pass
