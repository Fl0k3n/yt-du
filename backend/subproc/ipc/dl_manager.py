from backend.subproc.ipc.ipc_codes import DlCodes
from multiprocessing.connection import Connection
from backend.model.dl_task import DlTask
from typing import Deque, Dict, Generator, List
from backend.subproc.ipc.subproc_lifetime_observer import SubprocLifetimeObserver
from backend.subproc.ipc.message import DlData, Message, Messenger
from collections import deque
import multiprocessing as mp
from backend.subproc.yt_dl import YTDownloader
from backend.subproc.ipc.piped_status_observer import PipedStatusObserver


class StoredDlTask:
    def __init__(self, task: DlTask, task_id: int):
        self.task = task
        self.task_id = task_id

    def __eq__(self, other) -> bool:
        if isinstance(other, StoredDlTask):
            return self.task_id == other.task_id
        return False

    def __hash__(self) -> int:
        return hash(self.task_id)


class DlManager:
    def __init__(self, msger: Messenger):
        self.msger = msger
        self.MAX_BATCH_DL = 10
        self.subproc_obss: List[SubprocLifetimeObserver] = []

        self.task_queue: Deque[StoredDlTask] = deque()
        self.tasks: Dict[int, StoredDlTask] = {}
        self.connections: Dict[int, Connection] = {}

        self.handlers = {
            DlCodes.DL_STARTED: self._on_dl_started,
            DlCodes.CAN_PROCEED_DL: self._on_can_proceed_dl,
            DlCodes.CHUNK_FETCHED: self._on_chunk_fetched
        }

        self.id_gen = self._create_task_id_gen()

    def schedule_task(self, task: DlTask):
        tid = next(self.id_gen)
        s_task = StoredDlTask(task, tid)
        self.tasks[tid] = s_task

        self.task_queue.append(s_task)
        if len(self.task_queue) < self.MAX_BATCH_DL:
            self._start_download(self.task_queue.popleft())

    def _start_download(self, s_task: StoredDlTask):
        task = s_task.task

        url = task.get_url()
        path = task.get_path()

        # for now only links with 2 dlinks are supported
        dlink1, dlink2 = task.get_media_urls()

        my_con, child_con = mp.Pipe(duplex=True)
        self.connections[s_task.task_id] = my_con

        proc = mp.Process(target=self._run_downloader, args=(
            path, url, dlink1, dlink2, child_con, s_task.task_id))
        proc.start()

        child_con.close()

        for obs in self.subproc_obss:
            obs.on_subproc_created(proc, my_con)

    def _on_chunk_fetched(self, dl_data: DlData):
        link_id, bytes_fetched = dl_data.data
        task = self._get_task(dl_data)
        task.chunk_fetched(link_id, bytes_fetched)

    def _on_can_proceed_dl(self, dl_data: DlData):
        link_id = dl_data.data
        task = self._get_task(dl_data)
        permission = task.dl_permission_requested(link_id)

        conn = self.connections[dl_data.task_id]
        resp_msg = Message(DlCodes.DL_PERMISSION, permission)

        self.msger.send(conn, resp_msg)

    def _on_dl_started(self, dl_data: DlData):
        link_id = dl_data.data
        task = self._get_task(dl_data)

        task.dl_started(link_id)

    def msg_rcvd(self, msg: Message):
        # key error raised on unsupported code
        self.handlers[msg.code](msg.data)

    def add_subproc_lifetime_observer(self, obs: SubprocLifetimeObserver):
        self.subproc_obss.append(obs)

    def _run_downloader(self, path: str, url: str, dlink1: str, dlink2: str,
                        conn: Connection, task_id: int):
        stat_obs = PipedStatusObserver(conn, task_id, Messenger())
        downloader = YTDownloader(
            path, url, [dlink1, dlink2], stat_obs, cleanup=False)
        downloader.download()

    def _create_task_id_gen(self) -> Generator[int, None, None]:
        idx = 0
        while True:
            yield idx
            idx += 1

    def _get_task(self, dl_data: DlData) -> DlTask:
        return self.tasks[dl_data.task_id].task
