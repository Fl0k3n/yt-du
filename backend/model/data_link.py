from datetime import datetime
from backend.model.db_models import DB_DataLink, DB_DownloadErrorLog
from backend.utils.property import Property

try:
    from backend.model.playlist_link import PlaylistLink
except ImportError:
    # will happen because of cyclic imports, module needed only for type hints
    pass


class DataLink:
    def __init__(self, db_dlink: DB_DataLink, playlist_link: "PlaylistLink") -> None:
        self.db_dlink = db_dlink
        self.playlist_link = playlist_link
        self._setup_properties()

    def _setup_properties(self):
        self.dlink_id_property = Property[int](self.db_dlink.link_id)
        self.playlist_link_id_property = Property[int](
            self.db_dlink.playlist_link_id)
        self.url_property = Property[str](self.db_dlink.url)
        self.mime_property = Property[str](self.db_dlink.mime)
        self.expire_property = Property[int](self.db_dlink.expire)
        self.path_property = Property[str](self.db_dlink.path)
        # in bytes
        self.size_property = Property[int](self.db_dlink.size)
        # in bytes
        self.dled_size_property = Property[int](
            self.db_dlink.downloaded)
        self.dl_start_time_property = Property[datetime](
            self.db_dlink.download_start_time)
        self.last_chunk_url_property = Property[str](
            self.db_dlink.last_chunk_url)

    def get_playlist_link(self) -> "PlaylistLink":
        return self.playlist_link

    def get_error_logs(self) -> DB_DownloadErrorLog:
        # TODO
        return self.db_dlink.error_logs

    def get_dlink_id(self) -> int:
        return self.dlink_id_property.get()

    def get_playlist_link_id(self) -> int:
        return self.playlist_link_id_property.get()

    def get_url(self) -> str:
        return self.url_property.get()

    def get_mime(self) -> str:
        return self.mime_property.get()

    def get_expire_timestamp(self) -> int:
        return self.expire_property.get()

    def get_path(self) -> str:
        return self.path_property.get()

    def get_size(self) -> int:
        return self.size_property.get()

    def get_dled_size(self) -> int:
        return self.dled_size_property.get()

    def get_dl_start_time(self) -> datetime:
        return self.dl_start_time_property.get()

    def get_last_chunk_url(self) -> str:
        return self.last_chunk_url_property.get()

    def set_url(self, url: str):
        self.db_dlink.url = url
        self.url_property.set(url)

    def set_expire_timestamp(self, timestamp: int):
        self.db_dlink.expire = timestamp
        self.expire_property.set(timestamp)

    def set_path(self, path: str):
        self.db_dlink.path = path
        self.path_property.set(path)

    def set_size(self, size: int):
        self.db_dlink.size = size
        self.size_property.set(size)

    def set_dled_size(self, dled_size: int):
        self.db_dlink.downloaded = dled_size
        self.dled_size_property.set(dled_size)

    def set_dl_start_time(self, starttime: datetime):
        self.db_dlink.download_start_time = starttime
        self.dl_start_time_property.set(starttime)

    def set_last_chunk_url(self, url: str):
        self.db_dlink.last_chunk_url = url
        self.last_chunk_url_property.set(url)

    def __str__(self) -> str:
        return f'<[Data Link] mime = {self.get_mime()} | downloaded = {self.dled_size_property.get()} | path = {self.get_path()}>'
