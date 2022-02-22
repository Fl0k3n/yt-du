from typing import Iterable
from abc import ABC, abstractmethod


class PlaylistFetchedObserver(ABC):
    @abstractmethod
    def on_playlist_fetched(self, playlist_id: int,
                            playlist_idxs: Iterable[int],
                            links: Iterable[str],
                            titles: Iterable[str],
                            data_links: Iterable[Iterable[str]]):
        pass
