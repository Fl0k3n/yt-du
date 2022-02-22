from pathlib import Path
from typing import List, Set
from backend.model.playlist_link import PlaylistLink
from backend.subproc.yt_dl import Resumer


class PlaylistLinkResumer(Resumer):
    def __init__(self, playlist_link: PlaylistLink):
        self.tmp_files_dir = playlist_link.get_tmp_files_dir()
        dlinks = playlist_link.get_data_links()
        self.links_count = len(dlinks)

        # TODO make this more readable
        self.dlink_paths, self.dlink_sizes, self.dlink_dled_sizes = tuple(
            zip(*[(dlink.get_path(), dlink.get_size(), dlink.get_dled_size())
                  for dlink in dlinks]))

        self.finished_dlinks_count = len([1
                                         for dled_size, dlink_size in zip(
                                             self.dlink_dled_sizes, self.dlink_sizes)
                                         if dled_size == dlink_size])

        self.resumed_urls: Set[str] = set()

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

    def set_resumed(self, url: str):
        self.resumed_urls.add(url)

    def is_resumed(self, url: str) -> bool:
        return url in self.resumed_urls
