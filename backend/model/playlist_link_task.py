from backend.controller.playlist_dl_manager import PlaylistDlManager
from typing import List
from backend.model.dl_task import DlTask
from backend.model.db_models import PlaylistLink


class PlaylistLinkTask(DlTask):
    def __init__(self, playlist_link: PlaylistLink, pl_dl_mgr: PlaylistDlManager,
                 dest_path: str, url: str, media_urls: List[str]):
        super().__init__(dest_path, url, media_urls)
        self.pl_dl_mgr = pl_dl_mgr
        self.playlistLink = playlist_link

    def dl_started(self):
        self.pl_dl_mgr.on_dl_started(self.playlistLink)
