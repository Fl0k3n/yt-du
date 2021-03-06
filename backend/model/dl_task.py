from typing import List
from abc import ABC, abstractmethod
from backend.model.data_link import DataLink
from backend.subproc.yt_dl import StatusCode, MediaURL, Resumer


class DlTask(ABC):
    def __init__(self, dest_path: str, url: str, data_links: List[DataLink]):
        self.dest_path = dest_path
        self.url = url
        self.data_links = data_links
        self.finished_dls = 0
        self.resumed = False
        self.resumer = None
        self.link_renewed_observer = None

    def resume(self, resumer: Resumer):
        self.resumed = True
        self.resumer = resumer

    def is_resumed(self) -> bool:
        return self.resumed

    def get_url(self) -> str:
        return self.url

    def get_path(self) -> str:
        return self.dest_path

    def get_media_urls(self) -> List[str]:
        return [link.get_url() for link in self.data_links]

    def get_resumer(self) -> Resumer:
        return self.resumer

    @abstractmethod
    def process_started(self, tmp_files_dir: str):
        pass

    @abstractmethod
    def dl_started(self, link_idx: int, abs_path: str):
        pass

    @abstractmethod
    def dl_permission_requested(self, link_idx: int) -> bool:
        pass

    @abstractmethod
    def chunk_fetched(self, link_idx: int, expected_bytes_to_fetch: int,
                      bytes_fetched: int, chunk_url: str):
        pass

    @abstractmethod
    def dl_finished(self, link_idx: int):
        pass

    @abstractmethod
    def merge_started(self):
        pass

    @abstractmethod
    def merge_finished(self, status: StatusCode, stderr: str):
        pass

    @abstractmethod
    def process_finished(self, success: bool):
        pass

    @abstractmethod
    def process_stopped(self):
        pass

    @abstractmethod
    def dl_error_occured(self, link_idx: int, exc_type: str, exc_msg: str):
        pass

    @abstractmethod
    def renew_link(self, task_id: int, link_idx: int,
                   media_url: MediaURL, last_successful: str):
        pass

    def are_all_downloads_finished(self) -> bool:
        return self.finished_dls == len(self.data_links)

    def __str__(self):
        return f'[DL TASK] {self.url} | {self.dest_path}'
