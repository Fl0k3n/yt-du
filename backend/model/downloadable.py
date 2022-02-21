from abc import ABC, abstractmethod
from re import L
from backend.model.data_status import DataStatus
from backend.model.downloadable_type import DownloadableType
from backend.utils.property import Property


class Downloadable(ABC):
    def _setup_properties(self):
        self.size_property = Property[int](0)
        self.dled_size_property = Property[int](0)
        self.resume_requested_property = Property[bool](False)
        self.pause_requested_property = Property[bool](False)

    @abstractmethod
    def get_downloaded_bytes(self) -> int:
        pass

    @abstractmethod
    def get_size_bytes(self) -> int:
        pass

    @abstractmethod
    def get_status(self) -> DataStatus:
        pass

    @abstractmethod
    def set_status(self, status: DataStatus):
        pass

    @abstractmethod
    def get_url(self) -> str:
        pass

    @abstractmethod
    def get_path(self) -> str:
        pass

    @abstractmethod
    def is_pausable(self) -> bool:
        pass

    @abstractmethod
    def is_resumable(self) -> bool:
        pass

    @abstractmethod
    def is_removable(self) -> bool:
        pass

    @abstractmethod
    def is_paused(self) -> bool:
        pass

    @abstractmethod
    def is_finished(self) -> bool:
        pass

    @abstractmethod
    def force_pause(self):
        pass

    @abstractmethod
    def get_downloadable_type(self) -> DownloadableType:
        pass

    @abstractmethod
    def get_url_property(self) -> Property[str]:
        pass

    @abstractmethod
    def get_status_property(self) -> Property[DataStatus]:
        pass

    @abstractmethod
    def get_path_property(self) -> Property[str]:
        pass

    def get_size_property(self) -> Property[int]:
        return self.size_property

    def get_dled_size_property(self) -> Property[int]:
        return self.dled_size_property

    def get_resume_requested_property(self) -> Property[bool]:
        return self.resume_requested_property

    def get_pause_requested_property(self) -> Property[bool]:
        return self.pause_requested_property

    def is_resume_requested(self) -> bool:
        return self.resume_requested_property.get()

    def set_resume_requested(self, resume_requested: bool):
        self.resume_requested_property.set(resume_requested)

    def is_pause_requested(self) -> bool:
        return self.pause_requested_property.get()

    def set_pause_requested(self, pause_requested: bool):
        self.pause_requested_property.set(pause_requested)

    def set_size(self, size: int):
        self.size_property.set(size)

    def get_size(self) -> int:
        return self.size_property.get()

    def set_dled_size(self, size: int):
        self.dled_size_property.set(size)

    def get_dled_size(self) -> int:
        return self.dled_size_property.get()

    def get_dl_progress(self) -> int:
        try:
            return self.dled_size_property.get() / self.size_property.get()
        except ZeroDivisionError:
            return 0

    @staticmethod
    def get_formatted_size(size_bytes: int) -> str:
        if size_bytes > 1073741824:  # GB
            size = f'{round(size_bytes / 1073741824 * 100) / 100} GB'
        elif size_bytes > 1048576:  # MB
            size = f'{round(size_bytes / 1048576 * 100) / 100} MB'
        else:
            size = f'{round(size_bytes / 1024 * 100) / 100} KB'

        return size

    @staticmethod
    def get_formatted_dl_speed(speed_mbps) -> str:
        return Downloadable.get_formatted_size(int(speed_mbps * 1048576)) + '/s'
