from abc import ABC, abstractmethod
from backend.model.data_status import DataStatus
from backend.utils.property import Property


class Downloadable(ABC):
    def __init__(self) -> None:
        self.resume_requested = False
        self.pause_requested = False

    def _setup_properties(self):
        self.size_property = Property(self.get_size_bytes())
        self.dled_size_property = Property(self.get_downloaded_bytes())

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

    def is_resume_requested(self) -> bool:
        return self.resume_requested

    def set_resume_requested(self, resume_requested: bool):
        self.resume_requested = resume_requested

    def is_pause_requested(self) -> bool:
        return self.pause_requested

    def set_pause_requested(self, pause_requested: bool):
        self.pause_requested = pause_requested

    def set_size(self, size: int):
        self.size_property.set(size)

    def get_size(self) -> int:
        return self.size_property.get()

    def set_dled_size(self, size: int):
        self.dled_size_property.set(size)

    def get_dled_size(self) -> int:
        return self.dled_size_property.get()

    def get_formatted_size(self) -> str:
        size_bytes = self.get_size_bytes()

        if size_bytes > 1073741824:  # GB
            size = f'{round(size_bytes / 1073741824 * 100) / 100} GB'
        else:
            size = f'{round(size_bytes / 1048576 * 100) / 100} MB'

        return size
