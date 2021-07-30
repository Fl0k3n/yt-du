from abc import ABC, abstractmethod
from backend.subproc.yt_dl import MediaURL


class LinkRenewedObserver(ABC):
    @abstractmethod
    def on_link_renewed(self, task_id: int, link_idx: int, renewed: MediaURL, is_consistent: bool):
        pass
