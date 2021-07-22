from backend.controller.playlist_dl_manager import PlaylistDlManager
from typing import List
from backend.model.dl_task import DlTask
from backend.model.db_models import DataLink, PlaylistLink


class PlaylistLinkTask(DlTask):
    def __init__(self, playlist_link: PlaylistLink, pl_dl_mgr: PlaylistDlManager,
                 dest_path: str, url: str, data_links: List[DataLink]):
        super().__init__(dest_path, url, data_links)
        self.pl_dl_mgr = pl_dl_mgr
        self.playlistLink = playlist_link

    def dl_started(self, link_idx: int):
        data_link = self.playlistLink.data_links[link_idx]
        self.pl_dl_mgr.on_dl_started(self.playlistLink, data_link)
