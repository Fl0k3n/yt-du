from typing import Iterable, List
from backend.model.data_link import DataLink
from backend.model.data_status import DataStatus
from backend.model.db_models import DB_PlaylistLink
from backend.model.downloadable import Downloadable
from backend.utils.property import Property

try:
    from backend.model.playlist import Playlist
except ImportError:
    # will happen because of cyclic imports, module needed only for type hints
    pass


class PlaylistLink(Downloadable):
    def __init__(self, db_link: DB_PlaylistLink, playlist: "Playlist") -> None:
        super().__init__()
        self.db_link = db_link
        self.data_links: List[DataLink] = []

        for db_dlink in self.db_link.data_links:
            dlink = DataLink(db_dlink, self)
            self.add_data_link(dlink)

        self.playlist = playlist
        self.dl_task_id = None
        self.link_dling_count = 0
        self._setup_properties()

    def _setup_properties(self):
        super()._setup_properties()
        self.link_id_property = Property(self.db_link.link_id)
        self.playlist_number_property = Property(self.db_link.playlist_number)
        self.url_property = Property(self.db_link.url)
        self.name_property = Property(self.db_link.title)
        self.playlist_id_property = Property(self.db_link.playlist_number)
        self.cleaned_up_property = Property(self.db_link.cleaned_up)
        self.status_property = Property(DataStatus(self.db_link.status))
        self.path_property = Property(self.db_link.path)
        self.tmp_files_dir_property = Property(self.db_link.tmp_files_dir)

    def set_dl_task_id(self, tid: int):
        self.dl_task_id = tid
        self.playlist.add_dling_link(self)

    def set_dl_task_finished(self):
        self.dl_task_id = None
        self.playlist.remove_dling_link(self)

    def set_link_dling_count(self, count: int):
        self.link_dling_count = count

    def get_link_dling_count(self) -> int:
        return self.link_dling_count

    def get_dl_task_id(self) -> int:
        return self.dl_task_id

    def get_playlist(self) -> "Playlist":
        return self.playlist

    def get_data_links(self) -> Iterable[DataLink]:
        return self.data_links

    def get_link_id(self) -> int:
        return self.link_id_property.get()

    def get_playlist_number(self) -> int:
        return self.playlist_number_property.get()

    def get_url(self) -> str:
        return self.url_property.get()

    def get_name(self) -> str:
        return self.name_property.get()

    def get_playlist_id(self) -> int:
        return self.playlist_id_property.get()

    def is_cleaned_up(self) -> bool:
        return self.cleaned_up_property.get()

    def get_status(self) -> DataStatus:
        return self.status_property.get()

    def get_path(self) -> str:
        return self.path_property.get()

    def get_tmp_files_dir(self) -> str:
        return self.tmp_files_dir_property.get()

    def is_finished(self) -> bool:
        return self.get_status() == DataStatus.FINISHED

    def is_paused(self) -> bool:
        return self.get_status() == DataStatus.PAUSED

    def is_pausable(self) -> bool:
        return not self.is_pause_requested() and \
            self.get_status() in {DataStatus.WAIT_FOR_DL,
                                  DataStatus.DOWNLOADING}

    def is_resumable(self) -> bool:
        return not self.is_resume_requested() and self.get_status() == DataStatus.PAUSED

    def is_removable(self) -> bool:
        # TODO
        return False

    def force_pause(self):
        if self.is_pausable():
            self.set_status(DataStatus.PAUSED)

    def set_playlist_number(self, num: int):
        self.db_link.playlist_number = num
        self.playlist_number_property.set(num)

    def set_url(self, url: str):
        self.db_link.url = url
        self.url_property.set(url)

    def set_name(self, name: str):
        self.db_link.title = name
        self.name_property.set(name)

    def set_cleaned_up(self, cleaned_up: bool):
        self.db_link.cleaned_up = cleaned_up
        self.cleaned_up_property.set(cleaned_up)

    def set_status(self, status: DataStatus):
        self.db_link.status = status.value
        self.status_property.set(status)

    def set_path(self, path: str):
        self.db_link.path = path
        self.path_property.set(path)

    def set_tmp_files_dir_path(self, path: str):
        self.db_link.tmp_files_dir = path
        self.tmp_files_dir_property.set(path)

    def get_downloaded_bytes(self) -> int:
        return sum(dlink.get_dled_size() for dlink in self.data_links)

    def get_size_bytes(self) -> int:
        return sum(dlink.get_size() for dlink in self.data_links)

    def add_data_link(self, dlink: DataLink):
        self.data_links.append(dlink)

        self.size_property.set(
            self.size_property.get() + dlink.size_property.get())
        self.dled_size_property.set(
            self.dled_size_property.get() + dlink.dled_size_property.get())

        dlink.size_property.add_property_changed_observer(
            callback=lambda old, new: self.size_property.set(
                self.size_property.get() - old + new))

        dlink.dled_size_property.add_property_changed_observer(
            callback=lambda old, new: self.dled_size_property.set(
                self.dled_size_property.get() - old + new))

    def __hash__(self):
        return hash(self.db_link.link_id)

    def __eq__(self, other):
        if type(self) == type(other):
            return self.db_link.link_id == other.db_link.link_id
        return False
