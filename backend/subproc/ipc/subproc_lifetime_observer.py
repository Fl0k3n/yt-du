from abc import ABC, abstractmethod
from multiprocessing import Process
from multiprocessing.connection import Connection


class SubprocLifetimeObserver(ABC):
    @abstractmethod
    def on_subproc_created(self, process: Process, con: Connection = None):
        pass

    @abstractmethod
    def on_subproc_finished(self, process: Process, con: Connection = None):
        pass

    @abstractmethod
    def on_termination_requested(self, process: Process, con: Connection = None):
        pass
