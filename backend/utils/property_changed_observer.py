from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class PropertyChangedObserver(ABC, Generic[T]):
    @abstractmethod
    def on_changed(self, previous_val: T, current_val: T):
        pass
