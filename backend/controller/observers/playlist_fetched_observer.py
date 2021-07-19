from abc import ABC, abstractmethod
from typing import Iterable


class PlaylistFetchedObserver(ABC):
    @abstractmethod
    def on_playlist_fetched(self, playlist_id: int, links: Iterable[str],
                            titles: Iterable[str],
                            data_links: Iterable[Iterable[str]]):
        pass
