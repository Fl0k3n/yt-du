import logging
from queue import Queue
from backend.controller.app_closed_observer import AppClosedObserver
from collections import defaultdict
from typing import Dict, Iterable, List, Set
from backend.model.link_created_observer import LinkCreatedObserver
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from backend.db.playlist_repo import PlaylistRepo
from backend.model.playlist import Playlist
from backend.model.playlist_link import PlaylistLink
from backend.subproc.yt_dl import create_media_url, UnsupportedURLError


class Task:
    def __init__(self, playlist_link: PlaylistLink, data_url: str) -> None:
        self.pl_link = playlist_link
        self.data_url = data_url


class DoneTask:
    def __init__(self, playlist_link: PlaylistLink, url: str, size: int, mime: str, expire: int):
        self.pl_link = playlist_link
        self.url = url
        self.size = size
        self.mime = mime
        self.expire = expire


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

                self.created.emit(DoneTask(
                    task.pl_link, url, size, media_url.get_mime(), media_url.get_expire_time()))
            except UnsupportedURLError as e:
                self.failed_to_create.emit(e)

    def stop(self):
        self.stopped = True

    def add_task(self, task: Task):
        self.tasks.put(task)


class LinkCreator(AppClosedObserver):
    def __init__(self, repo: PlaylistRepo) -> None:
        self.repo = repo
        # pl link -> queried urls to-be-created
        self.not_ready: Dict[PlaylistLink, Set[str]] = {}
        # playlist -> number of links added
        self.playlist_batches: Dict[Playlist, int] = defaultdict(lambda: 0)
        self._init_worker()

        self.link_created_observers: List[LinkCreatedObserver] = []

    def add_link_created_observer(self, obs: LinkCreatedObserver):
        self.link_created_observers.append(obs)

    def schedule_creation_task(self, playlist_link: PlaylistLink, dlinks: Iterable[str]):
        self.not_ready[playlist_link] = set(dlinks)
        self.playlist_batches[playlist_link.playlist] += 1

        for dlink in dlinks:
            logging.debug(
                f'scheduling link creation task for {dlink} within {playlist_link}')
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

        if pl_link.get_playlist().is_deleted():
            logging.debug(
                f'link created, but playlist was deleted, exiting. {pl_link}')
            return

        dlink = self.repo.create_data_link(
            pl_link, task.url, task.size, task.mime, task.expire)

        self.not_ready[pl_link].remove(task.url)

        if not self.not_ready[pl_link]:
            playlist = pl_link.playlist
            self.playlist_batches[playlist] -= 1
            all_done = self.playlist_batches[playlist] == 0

            self.not_ready.pop(pl_link)
            logging.debug(f'link ready. {pl_link}')
            for obs in self.link_created_observers:
                obs.on_link_created(pl_link, dlink, all_done)

    def on_app_closed(self):
        self.creator_worker.stop()
        self.creator_thread.terminate()
