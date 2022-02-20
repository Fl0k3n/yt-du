from abc import ABC, abstractmethod
from typing import List
from backend.model.db_models import DB_DataLink, DB_PlaylistLink


class PlaylistDlManager(ABC):
    @abstractmethod
    def on_process_started(self, playlist_link: DB_PlaylistLink, tmp_files_dir: str):
        pass

    @abstractmethod
    def on_dl_started(self, playlist_link: DB_PlaylistLink, data_link: DB_DataLink, abs_path: str):
        pass

    @abstractmethod
    def can_proceed_dl(self, playlist_link: DB_PlaylistLink, data_link: DB_DataLink) -> bool:
        pass

    @abstractmethod
    def on_dl_progress(self, playlist_link: DB_PlaylistLink,
                       data_link: DB_DataLink, bytes_fetched: int, chunk_url: str):
        pass

    # single data link
    @abstractmethod
    def on_data_link_dled(self, playlist_link: DB_PlaylistLink, data_link: DB_DataLink):
        pass

    # single link
    @abstractmethod
    def on_link_dled(self, playlist_link: DB_PlaylistLink):
        pass

    @abstractmethod
    def on_merge_started(self, playlist_link: DB_PlaylistLink):
        pass

    @abstractmethod
    def on_merge_finished(self, playlist_link: DB_PlaylistLink, status: int, stderr: str):
        pass

    @abstractmethod
    def on_process_finished(self, playlist_link: DB_PlaylistLink, success: bool):
        pass

    @abstractmethod
    def on_process_paused(self, playlist_link: DB_PlaylistLink):
        pass
