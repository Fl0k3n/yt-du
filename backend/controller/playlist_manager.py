from backend.subproc.pl_link_resumer import PlaylistLinkResumer
from backend.model.playlist_link_task import PlaylistLinkTask
from backend.controller.playlist_dl_manager import PlaylistDlManager
from pathlib import Path
from backend.subproc.ipc.ipc_manager import IPCManager
from typing import Dict, Iterable, List, Set
from backend.controller.db_handler import DBHandler
from backend.model.db_models import DataLink, Playlist, PlaylistLink
from backend.controller.observers.playlist_modified_observer import PlaylistModifiedObserver
from backend.controller.observers.playlist_fetched_observer import PlaylistFetchedObserver
from backend.model.data_status import DataStatus
from backend.subproc.yt_dl import create_media_url, UnsupportedURLError
import datetime
from collections import defaultdict


class PlaylistManager(PlaylistFetchedObserver, PlaylistDlManager):
    def __init__(self, db: DBHandler, ipc_mgr: IPCManager):
        self.db = db
        self.ipc_mgr = ipc_mgr

        self.ipc_mgr.add_playlist_fetched_observer(self)
        self.loaded_playlists: List[Playlist] = []  # list of loaded playlists
        # playlist_url -> idx in list above
        self.pl_url_map: Dict[str, int] = {}
        # playlist_id  -> idx in list above
        self.pl_idx_map: Dict[int, int] = {}

        self.pl_sizes: Dict[int, int] = {}  # playlist_id -> size in bytes
        # playlist_id -> dled size in bytes
        self.dled_pl_bytes: Dict[int, int] = {}

        self.pl_link_sizes: Dict[int, int] = {}  # link_id -> size in bytes
        # link_id -> dled size in bytes
        self.dled_link_bytes: Dict[int, int] = {}

        # playlist_id -> count of links currently downloading
        self.pl_dling_count: Dict[int, int] = {}

        # link_id -> count of data_links currently downloading
        self.link_dling_count: Dict[int, int] = {}

        # playlist_id -> {playlist_link -> task_id}
        # ids of scheduled link downloads for given playlist
        self.pl_tasks: Dict[int, Dict[PlaylistLink, int]] = {}

        # playlists that were requested to be paused
        self.pl_pause_requests: Set[Playlist] = set()
        # links that were requested to be paused
        self.link_pause_requests: Set[PlaylistLink] = set()
        # playlist -> # of links requested to be paused
        self.pl_links_pause_req_count: Dict[Playlist, int] = defaultdict(
            lambda: 0)

        # links that were requested to be resumed
        self.link_resume_requests: Set[PlaylistLink] = set()
        # playlists that were requested to be resumed
        self.pl_resume_requests: Set[Playlist] = set()

        self.pl_modified_observers: List[PlaylistModifiedObserver] = []

    def add_pl_modified_observer(self, obs: PlaylistModifiedObserver):
        self.pl_modified_observers.append(obs)

    def add_playlist(self, playlist: Playlist):
        playlist.set_status(DataStatus.WAIT_FOR_FETCH)
        self.db.add_playlist(playlist)
        self.db.commit()
        self._cache_playlist(playlist)
        self.ipc_mgr.query_playlist_links(playlist)

        for obs in self.pl_modified_observers:
            obs.playlist_added(playlist)

    def _cache_playlist(self, playlist: Playlist):
        if playlist is None:  # ???
            return
        idx = len(self.loaded_playlists)
        self.loaded_playlists.append(playlist)
        self.pl_url_map[playlist.url] = idx
        self.pl_idx_map[playlist.playlist_id] = idx

    def get_playlist(self, url: str = None, id: int = None) -> Playlist:
        # TODO make it less uqly
        if url is None and id is None:
            raise AttributeError('either url or id is required')

        stored = self._get_stored_playlist(url, id)
        if stored is not None:
            return stored

        playlist = self.db.get_playlist(url=url, id=id)
        self._cache_playlist(playlist)
        return playlist

    def get_playlists(self, offset: int = 0, limit: int = None) -> List[Playlist]:
        # TODO check if was cached
        playlists = self.db.get_playlists(offset, limit)
        # cache them
        return playlists

    def _get_stored_playlist(self, url: str = None, id: int = None) -> Playlist:
        if url is not None and url in self.pl_url_map:
            return self.loaded_playlists[self.pl_url_map[url]]

        if id is not None and id in self.pl_idx_map:
            return self.loaded_playlists[self.pl_idx_map[id]]

        return None

    def get_item_count(self) -> int:
        return self.db.get_playlist_count()  # + get_link_count?

    def on_playlist_fetched(self, playlist_id: int,
                            playlist_idxs: Iterable[int],
                            links: Iterable[str],
                            titles: Iterable[str],
                            data_links: Iterable[Iterable[str]]):

        playlist = self.get_playlist(id=playlist_id)
        playlist.set_status(DataStatus.WAIT_FOR_DL)
        link_task_ids = {}
        link_sizes = []
        pl_links = []

        for idx, link, title, dlinks in zip(playlist_idxs, links, titles, data_links):
            path = self._create_video_path(
                playlist.directory_path, title, idx)

            pl_link = PlaylistLink(
                playlist_number=idx, url=link, title=title, path=path)

            pl_link.set_status(DataStatus.WAIT_FOR_DL)
            pl_links.append(pl_link)
            pl_link.playlist = playlist
            playlist.links.append(pl_link)
            self.db.add_pl_link(pl_link)

            size = 0
            for dlink in dlinks:
                dl = self._create_data_link(dlink)
                self.db.add_data_link(dl)
                dl.link = pl_link
                pl_link.data_links.append(dl)
                size += dl.size

            link_sizes.append(size)

        self.db.commit()

        for link, size in zip(pl_links, link_sizes):
            self.pl_link_sizes[link.link_id] = size
            self.dled_link_bytes[link.link_id] = 0

        self.pl_sizes[playlist.playlist_id] = sum(link_sizes)
        self.dled_pl_bytes[playlist.playlist_id] = 0

        for pl_link in pl_links:
            task = PlaylistLinkTask(
                pl_link, self, pl_link.path, pl_link.url, pl_link.data_links)
            task_id = self.ipc_mgr.schedule_dl_task(task)
            link_task_ids[pl_link] = task_id

        for obs in self.pl_modified_observers:
            obs.playlist_links_added(playlist)

        self.pl_tasks[playlist_id] = link_task_ids

    def _create_data_link(self, url) -> DataLink:
        try:
            media_url = create_media_url(url)
            dl = DataLink(url=url, size=media_url.get_size(),
                          mime=media_url.get_mime(), expire=media_url.get_expire_time())
            return dl
        except UnsupportedURLError as e:
            print(e)
            exit(2)
            # TODO handle it

    def _create_video_path(self, directory_path: str, title: str,
                           playlist_idx: int = None) -> str:
        dir = Path(directory_path)

        filename = f'{title}.mp4'
        if playlist_idx is not None:
            filename = f'{playlist_idx}_{filename}'

        return str(dir.joinpath(filename).absolute())

    def on_process_started(self, playlist_link: PlaylistLink, tmp_files_dir: str):
        print('DL PROCESS STARTED FOR ', playlist_link.title)

        if playlist_link in self.link_resume_requests:
            self.link_resume_requests.remove(playlist_link)

        if playlist_link.playlist in self.pl_resume_requests:
            self.pl_resume_requests.remove(playlist_link.playlist)

        playlist_link.tmp_files_dir = tmp_files_dir
        self.db.commit()

    def on_dl_started(self, playlist_link: PlaylistLink, data_link: DataLink, abs_path: str):
        playlist = playlist_link.playlist
        pl_id = playlist.playlist_id
        link_id = playlist_link.link_id
        first_link = False
        first_data_link = False

        if link_id not in self.link_dling_count:
            self.link_dling_count[link_id] = 1
            playlist_link.set_status(DataStatus.DOWNLOADING)
            first_data_link = True
        else:
            self.link_dling_count[link_id] += 1

        # wont be called if count drops to 0 then gets resumed
        if pl_id not in self.pl_dling_count:
            self.pl_dling_count[pl_id] = 1
            playlist.set_status(DataStatus.DOWNLOADING)
            first_link = True
        else:
            self.pl_dling_count[pl_id] += 1

        data_link.download_start_time = datetime.datetime.now()
        data_link.path = abs_path
        self.db.commit()

        if first_data_link:
            print('DL STARTED for ', playlist_link.title)
            for obs in self.pl_modified_observers:
                obs.link_dl_started(playlist_link)

        if first_link:
            for obs in self.pl_modified_observers:
                obs.playlist_dl_started(playlist)

    def can_proceed_dl(self, playlist_link: PlaylistLink, data_link: DataLink) -> bool:
        return playlist_link not in self.link_pause_requests

    def on_dl_progress(self, playlist_link: PlaylistLink,
                       data_link: DataLink, bytes_fetched: int, chunk_url: str):
        if playlist_link.link_id not in self.dled_link_bytes:
            self._cache_dled_link_bytes(playlist_link)

        if playlist_link.playlist_id not in self.dled_pl_bytes:
            self._cache_dled_playlist_bytes(playlist_link.playlist)

        self.dled_pl_bytes[playlist_link.playlist_id] += bytes_fetched
        self.dled_link_bytes[playlist_link.link_id] += bytes_fetched
        data_link.downloaded += bytes_fetched
        data_link.last_chunk_url = chunk_url

        self.db.commit()

        for obs in self.pl_modified_observers:
            obs.playlist_dl_progressed(playlist_link.playlist, playlist_link)

    def _cache_link_size(self, playlist_link: PlaylistLink):
        size = playlist_link.get_size_bytes()
        self.pl_link_sizes[playlist_link.link_id] = size

    def _cache_playlist_size(self, playlist: Playlist):
        size = 0
        for link in playlist.links:
            if link.link_id not in self.pl_link_sizes:
                self._cache_link_size(link)
            size += self.pl_link_sizes[link.link_id]
        self.pl_sizes[playlist.playlist_id] = size

    def _cache_dled_link_bytes(self, playlist_link: PlaylistLink):
        size = playlist_link.get_downloaded_bytes()
        self.dled_link_bytes[playlist_link.link_id] = size

    def _cache_dled_playlist_bytes(self, playlist: Playlist):
        size = 0
        for link in playlist.links:
            if link.link_id not in self.dled_link_bytes:
                self._cache_dled_link_bytes(link)
            size += self.dled_link_bytes[link.link_id]
        self.dled_pl_bytes[playlist.playlist_id] = size

    def _clear_link_dl_cache(self, playlist_link: PlaylistLink):
        self.dled_link_bytes.pop(playlist_link.link_id)

    def get_playlist_size_bytes(self, playlist: Playlist) -> int:
        if playlist.playlist_id not in self.pl_sizes:
            self._cache_playlist_size(playlist)

        return self.pl_sizes[playlist.playlist_id]

    def get_playlist_downloaded_bytes(self, playlist: Playlist) -> int:
        if playlist.playlist_id not in self.dled_pl_bytes:
            self._cache_dled_playlist_bytes(playlist)
        return self.dled_pl_bytes[playlist.playlist_id]

    def get_link_size_bytes(self, playlist_link: PlaylistLink) -> int:
        if playlist_link.link_id not in self.pl_link_sizes:
            self._cache_link_size(playlist_link)
        return self.pl_link_sizes[playlist_link.link_id]

    def get_link_downloaded_bytes(self, playlist_link: PlaylistLink) -> int:
        if playlist_link.link_id not in self.dled_link_bytes:
            self._cache_dled_link_bytes(playlist_link)
        return self.dled_link_bytes[playlist_link.link_id]

    def on_data_link_dled(self, playlist_link: PlaylistLink, data_link: DataLink):
        print(
            f'finished downloading {data_link.mime} for {playlist_link.title}')
        self.link_dling_count[playlist_link.link_id] -= 1

    def on_link_dled(self, playlist_link: PlaylistLink):
        self._clear_link_dl_cache(playlist_link)
        pl_id = playlist_link.playlist_id
        self.pl_dling_count[pl_id] -= 1
        self.link_dling_count.pop(playlist_link.link_id)
        playlist_link.set_status(DataStatus.WAIT_FOR_MERGE)
        self.db.commit()

        for obs in self.pl_modified_observers:
            obs.playlist_link_dled(playlist_link)

    def on_merge_started(self, playlist_link: PlaylistLink):
        playlist_link.set_status(DataStatus.MERGING)
        self.db.commit()

        for obs in self.pl_modified_observers:
            obs.playlist_link_merging(playlist_link)

    def on_merge_finished(self, playlist_link: PlaylistLink, status: int, stderr: str):
        pass  # TODO create merge data obj and save to db

    def on_process_finished(self, playlist_link: PlaylistLink, success: bool):
        # TODO
        playlist_link.set_status(DataStatus.FINISHED)
        playlist_link.cleaned_up = True
        self.db.commit()

        for obs in self.pl_modified_observers:
            obs.playlist_link_finished(playlist_link)

        pl_id = playlist_link.playlist.playlist_id
        self.pl_tasks[pl_id].pop(playlist_link)

        playlist = playlist_link.playlist

        if self._is_playlist_finished(playlist):
            playlist.set_status(DataStatus.FINISHED)
            self.db.commit()

            for obs in self.pl_modified_observers:
                obs.playlist_finished(playlist)
        elif self._is_playlist_paused(playlist):
            playlist.set_status(DataStatus.PAUSED)
            self.db.commit()

            for obs in self.pl_modified_observers:
                obs.playlist_paused(playlist)

    def on_process_paused(self, playlist_link: PlaylistLink):
        self.link_pause_requests.remove(playlist_link)
        self.pl_links_pause_req_count[playlist_link.playlist] -= 1
        self.pl_tasks[playlist_link.playlist.playlist_id].pop(playlist_link)

        playlist_link.set_status(DataStatus.PAUSED)
        self.link_dling_count.pop(playlist_link.link_id)

        for obs in self.pl_modified_observers:
            obs.playlist_link_paused(playlist_link)

        playlist = playlist_link.playlist

        if self._is_playlist_paused(playlist):
            playlist.set_status(DataStatus.PAUSED)
            self.pl_dling_count.pop(playlist.playlist_id)

            for obs in self.pl_modified_observers:
                obs.playlist_paused(playlist)

            try:
                self.pl_pause_requests.remove(playlist)
            except KeyError:  # links were queried for pause individually
                pass

        self.db.commit()

    # BRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR

    def on_playlist_pause_requested(self, playlist: Playlist):
        self.pl_pause_requests.add(playlist)

        not_running = []
        for link in self.pl_tasks[playlist.playlist_id].keys():
            running = self.on_link_pause_requested(link, inner_call=True)
            if not running:
                not_running.append(link)

        for link in not_running:
            link.set_status(DataStatus.PAUSED)
            for obs in self.pl_modified_observers:
                obs.playlist_link_paused(link)

        self.db.commit()

        for obs in self.pl_modified_observers:
            obs.playlist_pause_requested(playlist)

    def on_link_pause_requested(self, playlist_link: PlaylistLink, inner_call: bool = False) -> bool:
        task_id = self.pl_tasks[playlist_link.playlist.playlist_id][playlist_link]
        running = self.ipc_mgr.pause_dl(task_id)

        if running:
            self.pl_links_pause_req_count[playlist_link.playlist] += 1
            self.link_pause_requests.add(playlist_link)

        for obs in self.pl_modified_observers:
            obs.playlist_link_pause_requested(playlist_link)

        if not inner_call and not any(self.is_link_pausable(
                link) for link in playlist_link.playlist.links):
            for obs in self.pl_modified_observers:
                obs.playlist_pause_requested(playlist_link.playlist)

        return running

    def is_playlist_pausable(self, playlist: Playlist) -> bool:
        return playlist not in self.pl_pause_requests and \
            playlist.get_status() in {
                DataStatus.WAIT_FOR_DL, DataStatus.DOWNLOADING}

    def is_link_pausable(self, playlist_link: PlaylistLink) -> bool:
        return playlist_link not in self.link_pause_requests and \
            playlist_link.get_status() in {
                DataStatus.WAIT_FOR_DL, DataStatus.DOWNLOADING
            }

    def is_playlist_resumable(self, playlist: Playlist) -> bool:
        return playlist not in self.pl_resume_requests and \
            any(link.get_status() == DataStatus.PAUSED for link in playlist.links)

    def is_link_resumable(self, playlist_link: PlaylistLink) -> bool:
        return playlist_link not in self.link_resume_requests and \
            playlist_link.get_status() == DataStatus.PAUSED

    def _is_playlist_finished(self, playlist: Playlist) -> bool:
        return all(link.get_status() == DataStatus.FINISHED for link in playlist.links)

    def _is_playlist_paused(self, playlist: Playlist) -> bool:
        return all(link.get_status() in {DataStatus.FINISHED,
                                         DataStatus.PAUSED} for link in playlist.links)

    def on_link_resume_requested(self, playlist_link: PlaylistLink):
        self._resume_link(playlist_link)

    def on_playlist_resume_requested(self, playlist: Playlist):
        self.pl_resume_requests.add(playlist)

        for obs in self.pl_modified_observers:
            obs.playlist_resume_requested(playlist)

        for link in playlist.links:
            if self.is_link_resumable(link):
                self._resume_link(link)

    def _resume_link(self, playlist_link: PlaylistLink):
        self.link_resume_requests.add(playlist_link)

        resumer = PlaylistLinkResumer(playlist_link)
        task = PlaylistLinkTask(
            playlist_link, self, playlist_link.path, playlist_link.url, playlist_link.data_links)

        task.resume(resumer)
        task_id = self.ipc_mgr.schedule_dl_task(task)

        pl_id = playlist_link.playlist_id

        if pl_id not in self.pl_tasks:
            self.pl_tasks[pl_id] = {}
            # idk status resumed TODO

        self.pl_tasks[pl_id][playlist_link] = task_id

        for obs in self.pl_modified_observers:
            obs.playlist_link_resume_requested(playlist_link)
