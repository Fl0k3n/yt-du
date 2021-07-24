from abc import ABC, abstractmethod
from multiprocessing.connection import Connection
from multiprocessing import Process


class SubprocLifetimeObserver(ABC):
    @abstractmethod
    def on_subproc_created(self, process: Process, con: Connection = None):
        pass

    @abstractmethod
    def on_subproc_finished(self, process: Process, con: Connection = None):
        pass
