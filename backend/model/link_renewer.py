import logging
from collections import defaultdict, deque
from typing import Deque, Dict, Iterable, Set, Tuple
from backend.db.playlist_repo import PlaylistRepo
from backend.model.data_link import DataLink
from backend.model.playlist_link import PlaylistLink
from backend.model.link_fetched_observer import LinkFetchedObserver
from backend.subproc.yt_dl import MediaURL, UnsupportedURLError, create_media_url
from backend.subproc.ipc.ipc_manager import IPCManager


class LinkRenewer(LinkFetchedObserver):
    def __init__(self, ipc_mgr: IPCManager, repo: PlaylistRepo):
        self.ipc_mgr = ipc_mgr
        self.repo = repo

        self.renew_tasks: Dict[PlaylistLink,
                               Deque[Tuple[DataLink, int, int, MediaURL, str]]] = defaultdict(deque)

        # pl_link -> {mime -> raw MediaURL from renewed link}
        self.renewed_links: Dict[PlaylistLink,
                                 Dict[str, MediaURL]] = {}

        self.pending_requests: Set[PlaylistLink] = set()

        # if >= 1 data_link was inconsistent entire playlist will be considered inconsistent
        self.are_consistent: Dict[PlaylistLink, bool] = {}

    def set_consistent(self, playlist_link: PlaylistLink, is_consistent: bool):
        self.are_consistent[playlist_link] = is_consistent

    def is_consistent(self, playlist_link: PlaylistLink) -> bool:
        return self.are_consistent[playlist_link]

    def query_renewed_links(self, playlist_link: PlaylistLink, data_link: DataLink,
                            task_id: int, link_idx: int, media_url: MediaURL, last_successful: str):
        self.renew_tasks[playlist_link].append((
            data_link, task_id, link_idx, media_url, last_successful))
        if playlist_link in self.pending_requests:
            return

        if playlist_link in self.renewed_links and \
                media_url.get_mime() in self.renewed_links[playlist_link]:
            self._handle_queue(playlist_link)
        else:
            self.pending_requests.add(playlist_link)
            self.ipc_mgr.query_link(playlist_link)

    def _handle_queue(self, playlist_link: PlaylistLink):
        # TODO
        pq = self.renew_tasks[playlist_link]
        rl = self.renewed_links[playlist_link]

        while pq:
            data_link, task_id, link_idx, old_media_url, last_successful = pq.popleft()
            renewed_raw = rl.pop(old_media_url.get_mime())
            renewed, is_consistent = self._renew_link(
                playlist_link, data_link, old_media_url, renewed_raw, last_successful)
            self.ipc_mgr.on_link_renewed(
                task_id, link_idx, renewed, is_consistent)

    def on_link_fetched(self, original_link: PlaylistLink, data_links: Iterable[str]):
        self.pending_requests.remove(original_link)
        m_urls = (create_media_url(link) for link in data_links)

        self.renewed_links[original_link] = {
            url.get_mime(): url for url in m_urls}

        self._handle_queue(original_link)

    def _renew_link(self, playlist_link: PlaylistLink, data_link: DataLink, old: MediaURL,
                    renewed: MediaURL, last_successful: str) -> Tuple[MediaURL, bool]:

        is_consistent = self.is_consistent(
            playlist_link) and old.get_media_type() == renewed.get_media_type()

        if is_consistent:
            try:
                old.renew(renewed, last_successful)
                renewed = old
            except UnsupportedURLError:
                logging.exception(f'Failed to renew url for {playlist_link}')
                is_consistent = False

        logging.debug(
            f'link for {playlist_link} renewed successfully consistent={is_consistent}')

        data_link.set_url(renewed.get_raw_url())
        data_link.set_expire_timestamp(renewed.get_expire_time())

        if not is_consistent:
            data_link.set_size(renewed.get_size())
            # other params will be updated when dl finish for that link(from process mgr)

        self.repo.update()

        self.set_consistent(playlist_link, self.is_consistent(
            playlist_link) and is_consistent)

        return renewed, is_consistent
