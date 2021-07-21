from multiprocessing.connection import Connection
from os import stat
from backend.model.dl_task import DlTask
from typing import Deque, Dict, List
from backend.subproc.ipc.subproc_lifetime_observer import SubprocLifetimeObserver
from backend.subproc.ipc.message import Messenger
from collections import deque
import multiprocessing as mp
from backend.subproc.yt_dl import YTDownloader
from backend.subproc.ipc.piped_status_observer import PipedStatusObserver


class DlManager:
    def __init__(self, msger: Messenger):
        self.msger = msger
        self.MAX_BATCH_DL = 10
        self.subproc_obss: List[SubprocLifetimeObserver] = []

        self.task_queue: Deque[DlTask] = deque()

    def schedule_task(self, task):
        self.task_queue.append(task)
        if len(self.task_queue) < self.MAX_BATCH_DL:
            self._start_download(self.task_queue.popleft())

    def _start_download(self, task: DlTask):
        url = task.get_url()
        path = task.get_path()

        # for now only links with 2 dlinks are supported
        dlink1, dlink2 = task.get_media_urls()

        my_con, child_con = mp.Pipe(duplex=True)

        proc = mp.Process(target=self._run_downloader, args=(
            path, url, dlink1, dlink2, child_con))
        proc.start()

        child_con.close()

        for obs in self.subproc_obss:
            obs.on_subproc_created(proc, my_con)

        task.dl_started()

    def _on_download_finished(self):
        pass

    def add_subproc_lifetime_observer(self, obs: SubprocLifetimeObserver):
        self.subproc_obss.append(obs)

    def _run_downloader(self, path: str, url: str, dlink1: str, dlink2: str, conn: Connection):
        stat_obs = PipedStatusObserver(conn, Messenger())
        downloader = YTDownloader(
            path, url, [dlink1, dlink2], stat_obs, cleanup=False)
        downloader.download()
