from abc import ABC, abstractmethod
from backend.model.db_models import DataLink
from typing import List


class DlTask(ABC):
    def __init__(self, dest_path: str, url: str, data_links: List[DataLink]):
        self.dest_path = dest_path
        self.url = url
        self.data_links = data_links

    def get_url(self) -> str:
        return self.url

    def get_path(self) -> str:
        return self.dest_path

    def get_media_urls(self) -> List[str]:
        return [link.url for link in self.data_links]

    @abstractmethod
    def dl_started(self, link_idx: int):
        pass

    # @abstractmethod
    # def on_dl_progressed(self):
    #     pass

    def __str__(self):
        return f'[DL TASK] {self.url} | {self.dest_path}'
