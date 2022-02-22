import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, Set
from backend.model.data_status import DataStatus
from backend.model.db_models import DB_Playlist
from backend.model.downloadable import Downloadable
from backend.model.downloadable_type import DownloadableType
from backend.model.playlist_link import PlaylistLink
from backend.utils.observable_list import ObservableList
from backend.utils.property import Property


class Playlist(Downloadable):
    def __init__(self, db_playlist: DB_Playlist) -> None:
        super().__init__()
        self.db_playlist = db_playlist
        self.playlist_links = ObservableList[PlaylistLink]()
        self._setup_properties()

        for db_link in self.db_playlist.links:
            pl_link = PlaylistLink(db_link, self)
            self.add_playlist_link(pl_link)

        self.downloading_links: Set[PlaylistLink] = set()
        self.dling_count = 0
        self.deleted = False

    def _setup_properties(self):
        super()._setup_properties()
        self.playlist_id_property = Property[int](self.db_playlist.playlist_id)
        self.name_property = Property[str](self.db_playlist.name)
        self.url_property = Property[str](self.db_playlist.url)
        self.directory_path_property = Property[str](
            self.db_playlist.directory_path)
        self.added_at_property = Property[datetime](self.db_playlist.added_at)
        self.finished_at_property = Property[datetime](
            self.db_playlist.finished_at)
        self.status_property = Property[DataStatus](
            DataStatus(self.db_playlist.status))
        self.dl_speed_mbps_property = Property[float](0.0)

    def add_dling_link(self, playlist_link: PlaylistLink):
        self.downloading_links.add(playlist_link)

    def remove_dling_link(self, playlist_link: PlaylistLink):
        self.downloading_links.remove(playlist_link)

    def get_dl_speed_mbps(self) -> float:
        return self.dl_speed_mbps_property.get()

    def set_dl_speed_mbps(self, speed: float):
        self.dl_speed_mbps_property.set(speed)

    def is_downloading(self) -> bool:
        return self.dling_count > 0

    def set_deleted(self):
        self.deleted = True

    def is_deleted(self) -> bool:
        return self.deleted

    def get_downloading_links(self) -> Iterable[PlaylistLink]:
        return list(self.downloading_links)

    def set_dling_count(self, count: int):
        self.dling_count = count

    def get_dling_count(self) -> int:
        return self.dling_count

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
        return list(self.playlist_links)

    def get_playlist_links_obervable_list(self) -> ObservableList[PlaylistLink]:
        return self.playlist_links

    def get_downloadable_type(self) -> DownloadableType:
        return DownloadableType.PLAYLIST

    def get_downloaded_bytes(self) -> int:
        return sum(link.get_downloaded_bytes() for link in self.playlist_links)

    def get_size_bytes(self) -> int:
        return sum(link.get_size_bytes() for link in self.playlist_links)

    def get_url_property(self) -> Property[str]:
        return self.url_property

    def get_status_property(self) -> Property[DataStatus]:
        return self.status_property

    def get_path_property(self) -> Property[str]:
        return self.directory_path_property

    def get_name_property(self) -> Property[str]:
        return self.name_property

    def get_size_property(self) -> Property[int]:
        return self.size_property

    def get_dl_speed_mbps_property(self) -> Property[float]:
        return self.dl_speed_mbps_property

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

    def set_status(self, status: DataStatus):
        self.db_playlist.status = status.value
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
            self.set_status(DataStatus.PAUSED)

    # def __hash__(self):
    #     return hash(self.db_playlist.playlist_id)

    # def __eq__(self, other):
    #     if type(self) == type(other):
    #         return self.db_playlist.playlist_id == other.db_playlist.playlist_id
    #     return False

    def create_video_path(self, title: str, playlist_idx: int = None) -> str:
        dir = Path(self.directory_path_property.get())

        safe_title = re.sub(r'[^\w\s-]', '', title)
        safe_title = re.sub(r'[-\s]+', '-', safe_title).strip('-_')[:50]

        filename = f'{safe_title}.mp4'
        if playlist_idx is not None:
            filename = f'{playlist_idx}_{filename}'

        return str(dir.joinpath(filename).absolute())

    def __str__(self) -> str:
        return f'<[Playlist] name = {self.get_name()} | status = {self.get_status()}>'
