import time
from typing import Dict, List, Set
from collections import defaultdict
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from backend.model.playlist import Playlist
from backend.controller.app_closed_observer import AppClosedObserver


class Timer(QObject):
    tick = pyqtSignal()

    def __init__(self, clock_tick: float):
        super().__init__()
        self.stopped = False
        self.clock_tick = clock_tick

    def run(self):
        while True:
            time.sleep(self.clock_tick)
            if self.stopped:
                break
            self.tick.emit()

    def stop(self):
        self.stopped = True


class Speedo(AppClosedObserver):
    _CLOCK_TICK = 0.25  # each #seconds time is updated

    def __init__(self) -> None:
        # for how many seconds was downloading
        self.total_elapsed: Dict[Playlist, float] = defaultdict(lambda: 0.0)
        # bytes
        self.total_dled: Dict[Playlist, int] = defaultdict(lambda: 0)

        self.currently_tracked: Set[Playlist] = set()

        self.timer_thread = QThread()
        self.timer = Timer(self._CLOCK_TICK)
        self.timer.moveToThread(self.timer_thread)
        self.timer_thread.started.connect(self.timer.run)
        self.timer_thread.finished.connect(self.timer_thread.deleteLater)

        self.timer.tick.connect(self._on_tick)
        self.timer_thread.start()

    def dl_stopped(self, playlist: Playlist):
        self.currently_tracked.remove(playlist)

    def dl_resumed(self, playlist: Playlist):
        self.currently_tracked.add(playlist)

    def dl_progressed(self, playlist: Playlist, dled_bytes: int):
        self.total_dled[playlist] += dled_bytes

    def get_avg_speed_MBps(self, playlist: Playlist) -> float:
        delta_t = self.total_elapsed[playlist]
        size = self.total_dled[playlist]

        if delta_t == 0:
            return 0

        return round((size / 1048576) / delta_t * 100) / 100

    def _on_tick(self):
        for pl in self.currently_tracked:
            self.total_elapsed[pl] += self._CLOCK_TICK
            pl.set_dl_speed_mbps(self.get_avg_speed_MBps(pl))

    def on_app_closed(self):
        self.timer.stop()
        self.timer_thread.terminate()
