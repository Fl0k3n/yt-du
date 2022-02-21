from abc import ABC, abstractmethod


class ViewChangedObserver(ABC):
    @abstractmethod
    def on_changed_back(self):
        pass

    @abstractmethod
    def on_changed_forward(self):
        pass
