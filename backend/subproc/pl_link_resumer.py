from backend.model.db_models import PlaylistLink
from backend.model.data_status import DataStatus
from backend.subproc.yt_dl import Resumer
from pathlib import Path
from typing import List


class PlaylistLinkResumer(Resumer):
    def __init__(self, playlist_link: PlaylistLink):
        # that data should be cached so connection to db from another process
        # wont be made DI my *****
        self.tmp_files_dir = playlist_link.tmp_files_dir
        dlinks = playlist_link.data_links
        self.links_count = len(dlinks)

        self.dlink_paths, self.dlink_sizes, self.dlink_dled_sizes = tuple(
            zip(*[(dlink.path, dlink.size, dlink.downloaded)
                  for dlink in dlinks]))

        self.finished_dlinks_count = len([1
                                         for dled_size, dlink_size in zip(
                                             self.dlink_dled_sizes, self.dlink_sizes)
                                         if dled_size == dlink_size])

    def should_create_tmp_files_dir(self) -> bool:
        return self.tmp_files_dir is None

    def get_tmp_files_dir_path(self) -> Path:
        return Path(self.tmp_files_dir)

    def should_create_tmp_files(self) -> bool:
        return any(path is None for path in self.dlink_paths)

    def get_tmp_file_names(self) -> List[Path]:
        return [Path(path) for path in self.dlink_paths]

    def should_resume_download(self) -> bool:
        return self.finished_dlinks_count < self.links_count

    def get_finished_dlinks_count(self) -> int:
        return self.finished_dlinks_count
