from abc import ABC, abstractmethod
from typing import Any, Callable

from PyQt5.QtWidgets import QLineEdit


class Command(ABC):
    @abstractmethod
    def execute(self):
        pass


class CallRcvrCommand(Command):
    def __init__(self, receiver: Callable[..., any]):
        self.receiver = receiver

    def execute(self):
        self.receiver()
