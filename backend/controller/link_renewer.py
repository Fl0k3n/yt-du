from collections import defaultdict, deque
from backend.subproc.ipc.link_renewed_observer import LinkRenewedObserver
from backend.controller.observers.link_fetched_observer import LinkFetchedObserver
from typing import Deque, Dict, Iterable, Set, Tuple
from backend.subproc.yt_dl import MediaURL, UnsupportedURLError, create_media_url
from backend.model.db_models import DB_DataLink, DB_PlaylistLink
from backend.subproc.ipc.ipc_manager import IPCManager
from backend.controller.db_handler import DBHandler


class LinkRenewer(LinkFetchedObserver):
    def __init__(self, ipc_mgr: IPCManager, db: DBHandler):
        self.ipc_mgr = ipc_mgr
        self.db = db

        self.renew_tasks: Dict[DB_PlaylistLink,
                               Deque[Tuple[DB_DataLink, int, int, MediaURL, str]]] = defaultdict(deque)

        # pl_link -> {mime -> raw MediaURL from renewed link}
        self.renewed_links: Dict[DB_PlaylistLink,
                                 Dict[str, MediaURL]] = {}

        self.pending_requests: Set[DB_PlaylistLink] = set()

        # if >= 1 data_link was inconsistent entire playlist will
        self.are_consistent: Dict[DB_PlaylistLink, bool] = {}

    def set_consistent(self, playlist_link: DB_PlaylistLink, val: bool):
        self.are_consistent[playlist_link] = val

    def is_consistent(self, playlist_link: DB_PlaylistLink) -> bool:
        return self.are_consistent[playlist_link]

    def query_renewed_links(self, playlist_link: DB_PlaylistLink, data_link: DB_DataLink,
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

    def _handle_queue(self, playlist_link: DB_PlaylistLink):
        pq = self.renew_tasks[playlist_link]
        rl = self.renewed_links[playlist_link]

        while pq:
            data_link, task_id, link_idx, old_media_url, last_successful = pq.popleft()
            renewed_raw = rl.pop(old_media_url.get_mime())
            renewed, is_consistent = self._renew_link(
                playlist_link, data_link, old_media_url, renewed_raw, last_successful)
            self.ipc_mgr.on_link_renewed(
                task_id, link_idx, renewed, is_consistent)

    def on_link_fetched(self, original_link: DB_PlaylistLink, data_links: Iterable[str]):
        self.pending_requests.remove(original_link)
        m_urls = (create_media_url(link) for link in data_links)

        self.renewed_links[original_link] = {
            url.get_mime(): url for url in m_urls}

        self._handle_queue(original_link)

    def _renew_link(self, playlist_link: DB_PlaylistLink, data_link: DB_DataLink, old: MediaURL,
                    renewed: MediaURL, last_successful: str) -> Tuple[MediaURL, bool]:

        is_consistent = self.is_consistent(playlist_link) and type(
            renewed) == type(old)

        if is_consistent:
            try:
                old.renew(renewed, last_successful)
                renewed = old
            except UnsupportedURLError as e:
                print('Failed to renew url', e)
                is_consistent = False

        data_link.url = renewed.get_raw_url()
        data_link.expire = renewed.get_expire_time()

        if not is_consistent:
            data_link.size = renewed.get_size()
            # other params will be updated when dl finish for that link(from process mgr)

        self.db.commit()

        self.set_consistent(playlist_link, self.is_consistent(
            playlist_link) and is_consistent)

        return renewed, is_consistent
