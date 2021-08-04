from backend.controller.gui.app_closed_observer import AppClosedObserver
from collections import defaultdict
from backend.controller.db_handler import DBHandler
from typing import Dict, Iterable, List, Set
from backend.controller.link_created_observer import LinkCreatedObserver
from backend.model.db_models import DataLink, Playlist, PlaylistLink
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from backend.subproc.yt_dl import create_media_url, UnsupportedURLError
from queue import Queue


class Task:
    def __init__(self, playlist_link: PlaylistLink, data_url: str) -> None:
        self.pl_link = playlist_link
        self.data_url = data_url


class DoneTask:
    def __init__(self, playlist_link: PlaylistLink, dlink: DataLink):
        self.pl_link = playlist_link
        self.dlink = dlink


class LinkCreatorWorker(QObject):
    created = pyqtSignal(DoneTask)
    failed_to_create = pyqtSignal(UnsupportedURLError)

    def __init__(self):
        super().__init__()
        self.tasks = Queue()
        self.stopped = False

    def run(self):
        while not self.stopped:
            task = self.tasks.get(block=True)
            url = task.data_url

            try:
                media_url = create_media_url(url)
                size = media_url.get_size()

                dl = DataLink(url=url, size=size,
                              mime=media_url.get_mime(), expire=media_url.get_expire_time())

                self.created.emit(DoneTask(task.pl_link, dl))
            except UnsupportedURLError as e:
                self.failed_to_create.emit(e)

    def stop(self):
        self.stopped = True

    def add_task(self, task: Task):
        self.tasks.put(task)


class LinkCreator(AppClosedObserver):
    def __init__(self, db: DBHandler) -> None:
        self.db = db
        # pl link -> queried urls to-be-created
        self.not_ready: Dict[PlaylistLink, Set[str]] = {}
        # playlist -> number of links added
        self.playlist_batches: Dict[Playlist, int] = defaultdict(lambda: 0)
        self._init_worker()

        self.link_created_observers: List[LinkCreatedObserver] = []

    def add_link_created_observer(self, obs: LinkCreatedObserver):
        self.link_created_observers.append(obs)

    def add_playlist_link(self, playlist_link: PlaylistLink, dlinks: Iterable[str]):
        self.not_ready[playlist_link] = set(dlinks)
        self.playlist_batches[playlist_link.playlist] += 1

        for dlink in dlinks:
            self.creator_worker.add_task(Task(playlist_link, dlink))

    def _init_worker(self):
        self.creator_thread = QThread()
        self.creator_worker = LinkCreatorWorker()
        self.creator_worker.moveToThread(self.creator_thread)
        self.creator_thread.started.connect(self.creator_worker.run)
        self.creator_thread.finished.connect(self.creator_thread.deleteLater)

        self.creator_worker.created.connect(self._dlink_created)
        self.creator_worker.failed_to_create.connect(print)
        self.creator_thread.start()

    def _dlink_created(self, task: DoneTask):
        pl_link = task.pl_link
        dlink = task.dlink

        pl_link.data_links.append(dlink)
        self.db.add_data_link(dlink)
        dlink.link = pl_link
        pl_link.data_links.append(dlink)

        self.db.commit()

        self.not_ready[pl_link].remove(dlink.url)

        if not self.not_ready[pl_link]:
            playlist = pl_link.playlist
            self.playlist_batches[playlist] -= 1
            all_done = self.playlist_batches[playlist] == 0

            self.not_ready.pop(pl_link)
            for obs in self.link_created_observers:
                obs.on_link_created(pl_link, all_done)

    def on_app_closed(self):
        self.creator_worker.stop()
        self.creator_thread.terminate()
