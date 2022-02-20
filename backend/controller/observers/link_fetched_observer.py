from abc import ABC, abstractmethod
from backend.model.db_models import DB_PlaylistLink
from typing import Iterable


class LinkFetchedObserver(ABC):
    @abstractmethod
    def on_link_fetched(self, original_link: DB_PlaylistLink, data_links: Iterable[str]):
        pass
