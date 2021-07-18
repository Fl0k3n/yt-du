from abc import ABC, abstractmethod
from typing import Any, Callable

from PyQt5.QtWidgets import QLineEdit


class Command(ABC):
    @abstractmethod
    def execute(self):
        pass


class CallRcvrCommand(Command):
    def __init__(self, receiver: Callable[..., any], *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.receiver = receiver

    def execute(self):
        self.receiver(*self.args, **self.kwargs)
