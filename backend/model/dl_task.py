from abc import ABC, abstractmethod
from typing import List


class DlTask(ABC):
    def __init__(self, dest_path: str, url: str, media_urls: List[str]):
        self.dest_path = dest_path
        self.url = url
        self.media_urls = media_urls

    def get_url(self) -> str:
        return self.url

    def get_path(self) -> str:
        return self.dest_path

    def get_media_urls(self) -> List[str]:
        return self.media_urls

    @abstractmethod
    def dl_started(self):
        pass

    # @abstractmethod
    # def on_dl_progressed(self):
    #     pass

    def __str__(self):
        return f'[DL TASK] {self.url} | {self.dest_path}'
