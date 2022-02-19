from abc import ABC, abstractmethod
from typing import Any


class PropertyChangedObserver(ABC):
    @abstractmethod
    def on_changed(self, previous_val: Any, current_val: Any):
        pass
