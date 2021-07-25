from backend.subproc.ipc.ipc_codes import DlCodes
from multiprocessing.connection import Connection
from backend.model.dl_task import DlTask
from typing import Deque, Dict, Generator, List, Set
from backend.subproc.ipc.subproc_lifetime_observer import SubprocLifetimeObserver
from backend.subproc.ipc.message import DlData, Message, Messenger
from collections import deque
import multiprocessing as mp
from backend.subproc.yt_dl import YTDownloader
from backend.subproc.ipc.piped_status_observer import PipedStatusObserver
from backend.controller.gui.app_closed_observer import AppClosedObserver


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


class DlManager(AppClosedObserver):
    _MAX_BATCH_DL = 10

    def __init__(self, msger: Messenger):
        self.msger = msger
        self.subproc_obss: List[SubprocLifetimeObserver] = []

        self.task_queue: Deque[StoredDlTask] = deque()
        self.tasks: Dict[int, StoredDlTask] = {}

        self.connections: Dict[int, Connection] = {}
        self.processes: Dict[int, mp.Process] = {}

        self.paused_tasks: Set[StoredDlTask] = set()
        self.running_tasks: Set[StoredDlTask] = set()

        self.total_tasks_started = 0

        self.handlers = {
            DlCodes.DL_STARTED: self._on_dl_started,
            DlCodes.CAN_PROCEED_DL: self._on_can_proceed_dl,
            DlCodes.CHUNK_FETCHED: self._on_chunk_fetched,
            DlCodes.DL_FINISHED: self._on_dl_fisnished,
            DlCodes.MERGE_STARTED: self._on_merge_started,
            DlCodes.MERGE_FINISHED: self._on_merge_finished,
            DlCodes.PROCESS_FINISHED: self._on_process_finished,
            DlCodes.PROCESS_STOPPED: self._on_process_stopped
        }

        self.id_gen = self._create_task_id_gen()

    def schedule_task(self, task: DlTask) -> int:
        tid = next(self.id_gen)
        s_task = StoredDlTask(task, tid)
        self.tasks[tid] = s_task

        self.task_queue.append(s_task)
        self._check_queue()
        return tid

    def _check_queue(self):
        if self.task_queue and len(self.processes) < self._MAX_BATCH_DL:
            task = self.task_queue.popleft()
            if task not in self.paused_tasks:
                self._start_download(task)
            else:
                # task can be enqueued only once
                self.paused_tasks.remove(task)

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

        self.running_tasks.add(s_task)
        self.total_tasks_started += 1

        self.processes[s_task.task_id] = proc

        child_con.close()

        for obs in self.subproc_obss:
            obs.on_subproc_created(proc, my_con)

    def _on_dl_started(self, dl_data: DlData):
        link_id = dl_data.data
        task = self._get_task(dl_data)

        task.dl_started(link_id)

    def _on_can_proceed_dl(self, dl_data: DlData):
        link_id = dl_data.data
        task = self._get_task(dl_data)
        permission = task.dl_permission_requested(link_id)
        print('SENDING PERMISSION: ', permission)

        conn = self.connections[dl_data.task_id]
        resp_msg = Message(DlCodes.DL_PERMISSION, permission)

        self.msger.send(conn, resp_msg)

    def _on_chunk_fetched(self, dl_data: DlData):
        link_id, bytes_fetched = dl_data.data
        task = self._get_task(dl_data)
        task.chunk_fetched(link_id, bytes_fetched)

    def _on_dl_fisnished(self, dl_data: DlData):
        link_id = dl_data.data
        task = self._get_task(dl_data)
        task.dl_finished(link_id)

    def _on_merge_started(self, dl_data: DlData):
        self._get_task(dl_data).merge_started()

    def _on_merge_finished(self, dl_data: DlData):
        status, stderr = dl_data.data
        task = self._get_task(dl_data)
        task.merge_finished(status, stderr)

    def _clean_process_task(self, tid: int):
        process = self.processes.pop(tid)
        connection = self.connections.pop(tid)
        s_task = self.tasks.pop(tid)
        self.running_tasks.remove(s_task)

        for obs in self.subproc_obss:
            obs.on_subproc_finished(process, connection)

    def _on_process_finished(self, dl_data: DlData):
        success = dl_data.data
        task = self._get_task(dl_data)
        task.process_finished(success)
        tid = dl_data.task_id

        self._clean_process_task(tid)

        print('*'*100)
        print(
            f'TOTAL TASKS STARTED: {self.total_tasks_started} \
            PROC LEN IS {len(self.processes)} QUEUE LEN IS {len(self.task_queue)}')
        print('*'*100)

        self._check_queue()

    def _on_process_stopped(self, dl_data: DlData):
        # rcvd after process was paused
        task = self._get_task(dl_data)
        task.process_stopped()

        tid = dl_data.task_id
        self._clean_process_task(tid)
        self._check_queue()

    def msg_rcvd(self, msg: Message):
        # key error raised on unsupported code
        self.handlers[msg.code](msg.data)

    def add_subproc_lifetime_observer(self, obs: SubprocLifetimeObserver):
        self.subproc_obss.append(obs)

    def _run_downloader(self, path: str, url: str, dlink1: str, dlink2: str,
                        conn: Connection, task_id: int):
        stat_obs = PipedStatusObserver(conn, task_id, Messenger())
        downloader = YTDownloader(
            path, url, [dlink1, dlink2], stat_obs, cleanup=True)
        downloader.download()

    def _create_task_id_gen(self) -> Generator[int, None, None]:
        idx = 0
        while True:
            yield idx
            idx += 1

    def _get_task(self, dl_data: DlData) -> DlTask:
        return self.tasks[dl_data.task_id].task

    def on_app_closed(self):
        self.task_queue.clear()
        for tid, conn in self.connections.items():
            self.msger.send(conn, Message(DlCodes.TERMINATE))
            for obs in self.subproc_obss:
                obs.on_termination_requested(self.processes[tid], conn)

    def pause_task(self, tid: int) -> bool:
        """returns True if task was running """
        # only enqueued tasks wont be started
        # this has no effect on already running / finished ones
        try:
            task = self.tasks[tid]
            if task not in self.running_tasks:
                self.paused_tasks.add(task)
                return False
            return True
        except KeyError:
            print(f'Task {tid} is already finished')
