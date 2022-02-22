from abc import ABC, abstractmethod
from backend.model.data_link import DataLink
from backend.model.playlist_link import PlaylistLink


class PlaylistDlManager(ABC):
    @abstractmethod
    def on_process_started(self, playlist_link: PlaylistLink, tmp_files_dir: str):
        pass

    @abstractmethod
    def on_dl_started(self, playlist_link: PlaylistLink, data_link: DataLink, abs_path: str):
        pass

    @abstractmethod
    def can_proceed_dl(self, playlist_link: PlaylistLink, data_link: DataLink) -> bool:
        pass

    @abstractmethod
    def on_dl_progress(self, playlist_link: PlaylistLink,
                       data_link: DataLink, bytes_fetched: int, chunk_url: str):
        pass

    # single data link
    @abstractmethod
    def on_data_link_dled(self, playlist_link: PlaylistLink, data_link: DataLink):
        pass

    # single link
    @abstractmethod
    def on_link_dled(self, playlist_link: PlaylistLink):
        pass

    @abstractmethod
    def on_merge_started(self, playlist_link: PlaylistLink):
        pass

    @abstractmethod
    def on_merge_finished(self, playlist_link: PlaylistLink, status: int, stderr: str):
        pass

    @abstractmethod
    def on_process_finished(self, playlist_link: PlaylistLink, success: bool):
        pass

    @abstractmethod
    def on_process_paused(self, playlist_link: PlaylistLink):
        pass
