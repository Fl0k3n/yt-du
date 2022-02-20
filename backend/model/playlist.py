import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Set
from backend.model.data_status import DataStatus
from backend.model.db_models import DB_Playlist
from backend.model.downloadable import Downloadable
from backend.model.playlist_link import PlaylistLink
from backend.utils.observable_list import ObservableList
from backend.utils.property import Property


class Playlist(Downloadable):
    def __init__(self, db_playlist: DB_Playlist) -> None:
        super().__init__()
        self.db_playlist = db_playlist
        self.playlist_links: List[PlaylistLink] = ObservableList()

        for db_link in self.db_playlist.links:
            pl_link = PlaylistLink(db_link, self)
            self.add_playlist_link(pl_link)

        self._setup_properties()

        self.downloading_links: Set[PlaylistLink] = set()
        self.is_deleted = False
        self.dling_count = 0

    def _setup_properties(self):
        super()._setup_properties()
        self.playlist_id_property = Property(self.db_playlist.playlist_id)
        self.name_property = Property(self.db_playlist.name)
        self.url_property = Property(self.db_playlist.url)
        self.directory_path_property = Property(
            self.db_playlist.directory_path)
        self.added_at_property = Property(self.db_playlist.added_at)
        self.finished_at_property = Property(self.db_playlist.finished_at)
        self.status_property = Property(DataStatus(self.db_playlist.status))

    def add_dling_link(self, playlist_link: PlaylistLink):
        self.downloading_links.add(playlist_link)

    def remove_dling_link(self, playlist_link: PlaylistLink):
        self.downloading_links.remove(playlist_link)

    def get_downloading_links(self) -> Iterable[PlaylistLink]:
        return list(self.downloading_links)

    def set_dling_count(self, count: int):
        self.dling_count = count

    def get_dling_count(self) -> int:
        return self.dling_count

    def set_deleted(self):
        self.is_deleted = True

    def is_deleted(self) -> bool:
        return self.is_deleted

    def get_playlist_id(self) -> int:
        return self.playlist_id_property.get()

    def get_name(self) -> str:
        return self.name_property.get()

    def get_url(self) -> str:
        return self.url_property.get()

    def get_path(self) -> str:
        return self.directory_path_property.get()

    def get_added_at(self) -> datetime:
        return self.added_at_property.get()

    def get_finished_at(self) -> datetime:
        return self.finished_at_property.get()

    def get_status(self) -> DataStatus:
        return self.status_property.get()

    def get_playlist_links(self) -> Iterable[PlaylistLink]:
        return self.playlist_links

    def get_playlist_links_obervable_list(self) -> ObservableList:
        return self.playlist_links

    def set_name(self, name: str):
        self.db_playlist.name = name
        self.name_property.set(name)

    def set_url(self, url: str):
        self.db_playlist.url = url
        self.url_property.set(url)

    def set_directory_path(self, path: str):
        self.db_playlist.directory_path = path
        self.directory_path_property.set(path)

    def set_added_at(self, timestamp: datetime):
        self.db_playlist.added_at = timestamp
        self.added_at_property.set(timestamp)

    def set_finished_at(self, timestamp: datetime):
        self.db_playlist.finished_at = timestamp
        self.finished_at_property.set(timestamp)

    def _get_downloaded_bytes(self) -> int:
        return sum(link.get_downloaded_bytes() for link in self.playlist_links)

    def _get_size_bytes(self) -> int:
        return sum(link.get_size_bytes() for link in self.playlist_links)

    def set_status(self, status: DataStatus):
        self.status_property.set(status)

    def add_playlist_link(self, pl_link: PlaylistLink):
        self.playlist_links.append(pl_link)

        self.size_property.set(
            self.size_property.get() + pl_link.size_property.get())
        self.dled_size_property.set(
            self.dled_size_property.get() + pl_link.dled_size_property.get())

        pl_link.size_property.add_property_changed_observer(
            callback=lambda old, new: self.size_property.set(
                self.size_property.get() - old + new))

        pl_link.dled_size_property.add_property_changed_observer(
            callback=lambda old, new: self.dled_size_property.set(
                self.dled_size_property.get() - old + new))

    def is_paused(self) -> bool:
        return self.get_status() == DataStatus.PAUSED or \
            all(playlist_link.is_paused() or playlist_link.is_finished()
                for playlist_link in self.playlist_links)

    def is_finished(self) -> bool:
        return self.get_status() == DataStatus.FINISHED or \
            all(playlist_link.is_finished()
                for playlist_link in self.playlist_links)

    def is_pausable(self) -> bool:
        return not self.is_pause_requested() and \
            self.get_status() in {DataStatus.WAIT_FOR_DL,
                                  DataStatus.DOWNLOADING}

    def is_removable(self) -> bool:
        return self.get_status() in {DataStatus.WAIT_FOR_FETCH, DataStatus.PAUSED, DataStatus.FINISHED}

    def is_resumable(self) -> bool:
        return not self.is_resume_requested() and \
            any(link.is_resumable() for link in self.playlist_links)

    def force_pause(self):
        if self.is_pausable():
            for link in self.playlist_links:
                link.force_pause()

    def __hash__(self):
        return hash(self.db_playlist.playlist_id)

    def __eq__(self, other):
        if type(self) == type(other):
            return self.db_playlist.playlist_id == other.db_playlist.playlist_id
        return False

    def create_video_path(self, title: str, playlist_idx: int = None) -> str:
        dir = Path(self.directory_path_property.get())

        safe_title = re.sub(r'[^\w\s-]', '', title)
        safe_title = re.sub(r'[-\s]+', '-', safe_title).strip('-_')[:50]

        filename = f'{safe_title}.mp4'
        if playlist_idx is not None:
            filename = f'{playlist_idx}_{filename}'

        return str(dir.joinpath(filename).absolute())
