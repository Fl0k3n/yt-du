from typing import Any, Dict, Set, Tuple
from backend.subproc.yt_dl import MediaURL, StatusObserver, UnsupportedURLError, create_media_url
from backend.subproc.ipc.message import Message, Messenger, DlData
from backend.subproc.ipc.ipc_codes import DlCodes
from multiprocessing.connection import Connection
import threading
from signal import SIGINT
import os


class PipedStatusObserver(StatusObserver):
    def __init__(self, conn: Connection, task_id: int, msger: Messenger):
        self.msger = msger
        self.task_id = task_id
        self.conn = conn
        self.sender_lock = threading.Lock()

        self.exit_lock = threading.Lock()
        self.exit_allowed_cond = threading.Condition(self.exit_lock)
        self.thread_count = 1  # excluding listener thread of this class
        self.exit_allowed_by = 1
        self.exiting = False

        self.child_pids: Set[int] = set()
        self.children_lock = threading.Lock()

        # link_idx -> permission
        self.dl_permissions: Dict[int, bool] = {}
        self.permission_lock = threading.Lock()
        self.dl_perm_cond = threading.Condition(self.permission_lock)

        self.listener = threading.Thread(
            target=self._listen_for_msgs, daemon=True)

        self.renew_links_lock = threading.Lock()
        self.links_renewed_cond = threading.Condition(self.renew_links_lock)
        # link_idx -> (renewed MediaUrl, is_consistent)
        self.renewed_links: Dict[int, Tuple[MediaURL, bool]] = {}

        self.listener.start()

    def process_started(self, tmp_files_dir_path: str):
        self._send_dl_msg(DlCodes.PROCESS_STARTED, tmp_files_dir_path)

    def dl_started(self, idx: int, abs_path: str):
        self._send_dl_msg(DlCodes.DL_STARTED, (idx, abs_path))

    def dl_finished(self, idx: int):
        self._send_dl_msg(DlCodes.DL_FINISHED, idx)

    def chunk_fetched(self, idx: int, bytes_len: int, chunk_link: str):
        self._send_dl_msg(DlCodes.CHUNK_FETCHED, (idx, bytes_len, chunk_link))

    def can_proceed_dl(self, idx: int) -> bool:
        if self.exiting:
            return False

        self._send_dl_msg(DlCodes.CAN_PROCEED_DL, idx)

        with self.permission_lock:
            while idx not in self.dl_permissions:
                self.dl_perm_cond.wait()
            return self.dl_permissions.pop(idx)

    def process_stopped(self):
        msg = self._create_dl_msg(DlCodes.PROCESS_STOPPED, None)
        self.msger.send(self.conn, msg)

    def merge_started(self):
        msg = self._create_dl_msg(DlCodes.MERGE_STARTED, None)
        self.msger.send(self.conn, msg)

    def merge_finished(self, status: int, stderr: str):
        msg = self._create_dl_msg(DlCodes.MERGE_FINISHED, (status, stderr))
        self.msger.send(self.conn, msg)

    def process_finished(self, success: bool):
        msg = self._create_dl_msg(DlCodes.PROCESS_FINISHED, success)
        self.msger.send(self.conn, msg)

    def failed_to_init(self, exc_type: str, exc_msg: str):
        print('[PIPED] init error')

    def dl_error_occured(self, idx: int, exc_type: str, exc_msg: str):
        self._send_dl_msg(DlCodes.DL_ERROR, (idx, exc_type, exc_msg))

    def _create_dl_msg(self, code: DlCodes, data: Any) -> DlData:
        return Message(code, DlData(self.task_id, data))

    def _send_dl_msg(self, code: DlCodes, data: Any):
        msg = self._create_dl_msg(code, data)
        with self.sender_lock:
            self.msger.send(self.conn, msg)

    def _listen_for_msgs(self):
        while True:
            msg = self.msger.recv(self.conn)
            if msg.code == DlCodes.TERMINATE:
                with self.exit_lock:
                    while self.exit_allowed_by < self.thread_count:
                        self.exit_allowed_cond.wait()
                    self.exiting = True

                with self.children_lock:
                    for pid in self.child_pids:
                        os.kill(pid, SIGINT)
                    os._exit(0)  # TODO maybe use another exit method
            elif msg.code == DlCodes.DL_PERMISSION:
                with self.permission_lock:
                    link_idx, perm = msg.data
                    self.dl_permissions[link_idx] = perm
                    self.dl_perm_cond.notify_all()
            elif msg.code == DlCodes.URL_RENEWED:
                with self.renew_links_lock:
                    idx, media_url, is_consistent = msg.data
                    self.renewed_links[idx] = (media_url, is_consistent)
                    self.links_renewed_cond.notify_all()
            else:
                print('rcvd unexpected msg:', msg)

    def thread_started(self):
        self.thread_count += 1

    def thread_finished(self):
        self.thread_count -= 1
        if self.thread_count < 1:
            raise RuntimeError('More threads exited that have been started')

    def forbid_exit(self):
        with self.exit_lock:
            self.exit_allowed_by -= 1

    def allow_exit(self):
        with self.exit_lock:
            self.exit_allowed_by += 1
            self.exit_allowed_cond.notify_all()

    def allow_subproc_start(self):
        self.children_lock.acquire()

    def subprocess_started(self, pid: int):
        # called after asking for permission so lock is held
        self.child_pids.add(pid)
        self.children_lock.release()

    def subprocess_finished(self, pid: int):
        with self.children_lock:
            self.child_pids.remove(pid)

    def renew_link(self, idx: int, media_url: MediaURL, last_successful: str) -> Tuple[MediaURL, bool]:
        self._send_dl_msg(DlCodes.URL_EXPIRED,
                          (idx, media_url, last_successful))

        with self.renew_links_lock:
            while idx not in self.renewed_links:
                self.links_renewed_cond.wait()

            renewed, is_consistent = self.renewed_links.pop(idx)

            return renewed, is_consistent
