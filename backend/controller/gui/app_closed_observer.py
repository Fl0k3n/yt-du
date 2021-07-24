from abc import ABC, abstractmethod


class AppClosedObserver(ABC):
    @abstractmethod
    def on_app_closed(self):
        pass
