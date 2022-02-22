import logging
from typing import List
from backend.model.playlist_link import PlaylistLink
from backend.model.link_renewer import LinkRenewer
from backend.subproc.yt_dl import StatusCode, MediaURL
from backend.model.playlist_dl_manager import PlaylistDlManager
from backend.model.dl_task import DlTask


class PlaylistLinkTask(DlTask):
    def __init__(self, playlist_link: PlaylistLink, pl_dl_mgr: PlaylistDlManager,
                 link_renewer: LinkRenewer):
        super().__init__(playlist_link.get_path(),
                         playlist_link.get_url(), playlist_link.get_data_links())
        self.pl_dl_mgr = pl_dl_mgr
        self.link_renewer = link_renewer
        self.playlist_link = playlist_link
        self.finished_dls = 0
        # mime -> renewed datalink(raw) converted to MediaURL

    def process_started(self, tmp_files_dir: str):
        self.pl_dl_mgr.on_process_started(self.playlist_link, tmp_files_dir)

    def dl_started(self, link_idx: int, abs_path: str):
        data_link = self.data_links[link_idx]
        self.pl_dl_mgr.on_dl_started(self.playlist_link, data_link, abs_path)

    def dl_permission_requested(self, link_idx: int) -> bool:
        data_link = self.data_links[link_idx]
        return self.pl_dl_mgr.can_proceed_dl(self.playlist_link, data_link)

    def chunk_fetched(self, link_idx: int, expected_bytes_to_fetch: int,
                      bytes_fetched: int, chunk_url: str):
        data_link = self.data_links[link_idx]
        self.pl_dl_mgr.on_dl_progress(
            self.playlist_link,
            data_link,
            expected_bytes_to_fetch,
            bytes_fetched,
            chunk_url)

    def dl_finished(self, link_idx: int):
        data_link = self.data_links[link_idx]
        self.pl_dl_mgr.on_data_link_dled(self.playlist_link, data_link)

        self.finished_dls += 1
        if self.are_all_downloads_finished():
            self.pl_dl_mgr.on_link_dled(self.playlist_link)

    def merge_started(self):
        self.pl_dl_mgr.on_merge_started(self.playlist_link)

    def merge_finished(self, status: StatusCode, stderr: str):
        self.pl_dl_mgr.on_merge_finished(self.playlist_link, status, stderr)

    def process_finished(self, success: bool):
        self.pl_dl_mgr.on_process_finished(self.playlist_link, success)

    def process_stopped(self):
        self.pl_dl_mgr.on_process_paused(self.playlist_link)

    def renew_link(self, task_id: int, link_idx: int,
                   media_url: MediaURL, last_successful: str):
        self.link_renewer.query_renewed_links(self.playlist_link,
                                              self.data_links[link_idx], task_id,
                                              link_idx, media_url, last_successful)

    def dl_error_occured(self, link_idx: int, exc_type: str, exc_msg: str):
        # TODO
        data_link = self.data_links[link_idx]
        logging.error(
            f'[DL ERROR] for {data_link.get_playlist_link()} | {data_link} | exc_type = {exc_type} | error msg = {exc_msg}')

    def get_media_urls(self) -> List[str]:
        if not self.resumed:
            return super().get_media_urls()

        m_urls = []
        for dlink in self.data_links:
            url = dlink.get_url()
            if dlink.get_last_chunk_url() is not None:
                url = dlink.get_last_chunk_url()
                self.resumer.set_resumed(url)
            m_urls.append(url)

        return m_urls
