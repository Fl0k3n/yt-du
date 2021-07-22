from backend.model.playlist_link_task import PlaylistLinkTask
from backend.controller.playlist_dl_manager import PlaylistDlManager
from pathlib import Path
from backend.subproc.ipc.ipc_manager import IPCManager
from typing import Iterable, List
from backend.controller.db_handler import DBHandler
from backend.model.db_models import DataLink, Playlist, PlaylistLink
from backend.controller.observers.playlist_modified_observer import PlaylistModifiedObserver
from backend.controller.observers.playlist_fetched_observer import PlaylistFetchedObserver
import urllib.parse as parse
import datetime


class PlaylistManager(PlaylistFetchedObserver, PlaylistDlManager):
    def __init__(self, db: DBHandler, ipc_mgr: IPCManager):
        self.db = db
        self.ipc_mgr = ipc_mgr

        self.ipc_mgr.add_playlist_fetched_observer(self)
        self.loaded_playlists = []  # list of loaded playlists
        self.pl_url_map = {}  # playlist_url -> idx in list above
        self.pl_idx_map = {}  # playlist_id  -> idx in list above

        self.pl_modified_observers = []

    def add_pl_modified_observer(self, obs: PlaylistModifiedObserver):
        self.pl_modified_observers.append(obs)

    def add_playlist(self, playlist: Playlist):
        self.db.add_playlist(playlist)
        self.db.commit()
        self._cache_playlist(playlist)
        self.ipc_mgr.query_playlist_links(playlist)

        for obs in self.pl_modified_observers:
            obs.playlist_added(playlist)

    def _cache_playlist(self, playlist: Playlist):
        if playlist is None:
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
        pl_links = []

        for idx, link, title, dlinks in zip(playlist_idxs, links, titles, data_links):
            pl_link = PlaylistLink(
                playlist_number=idx, url=link, title=title)
            pl_links.append(pl_link)
            pl_link.playlist = playlist
            playlist.links.append(pl_link)
            self.db.add_pl_link(pl_link)

            for dlink in dlinks:
                dl = self._create_data_link(dlink)
                dl.link = pl_link
                pl_link.data_links.append(dl)
                self.db.add_data_link(dl)

        self.db.commit()

        for obs in self.pl_modified_observers:
            obs.playlist_links_added(playlist)

        for pl_link in pl_links:
            path = self._create_video_path(
                playlist.directory_path, pl_link.title, pl_link.playlist_number)
            task = PlaylistLinkTask(
                pl_link, self, path, pl_link.url, pl_link.data_links)
            self.ipc_mgr.schedule_dl_task(task)

    def _create_data_link(self, url) -> DataLink:
        query = parse.urlparse(url).query
        params = parse.parse_qs(query)

        try:
            size = params['clen'][0]
            mime = params['mime'][0]
            expire = params['expire'][0]

            dl = DataLink(url=url, size=size, mime=mime, expire=expire)
            return dl
        except KeyError:
            print('Failed to extract ', url)

    def _create_video_path(self, directory_path: str, title: str,
                           playlist_idx: int = None) -> str:
        dir = Path(directory_path)

        filename = f'{title}.mp4'
        if playlist_idx is not None:
            filename = f'{playlist_idx}_{filename}'

        return str(dir.joinpath(filename).absolute())

    def on_dl_started(self, playlist_link: PlaylistLink, data_link: DataLink):
        print('DL STARTED for ', playlist_link.title)
        data_link.download_start_time = datetime.datetime.now()
