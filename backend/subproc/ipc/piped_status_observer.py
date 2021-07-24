from typing import Any
from backend.subproc.yt_dl import StatusObserver
from backend.subproc.ipc.message import Message, Messenger, DlData
from backend.subproc.ipc.ipc_codes import DlCodes
from multiprocessing.connection import Connection
import threading
import os
from queue import Queue


class PipedStatusObserver(StatusObserver):
    def __init__(self, conn: Connection, task_id: int, msger: Messenger):
        self.msger = msger
        self.task_id = task_id
        self.conn = conn
        self.sender_lock = threading.Lock()

        self.exit_lock = threading.Lock()
        self.exit_allowed_cond = threading.Condition(self.exit_lock)
        self.thread_count = 1
        self.exit_allowed_by = 1
        self.exiting = False

        self.msg_queue = Queue()

        self.listener = threading.Thread(
            target=self._listen_for_msgs, daemon=True).start()

    def dl_started(self, idx: int):
        self._send_dl_msg(DlCodes.DL_STARTED, idx)

    def dl_finished(self, idx: int):
        self._send_dl_msg(DlCodes.DL_FINISHED, idx)

    def chunk_fetched(self, idx: int, bytes_len: int):
        self._send_dl_msg(DlCodes.CHUNK_FETCHED, (idx, bytes_len))

    def can_proceed_dl(self, idx: int) -> bool:
        if self.exiting:
            return False

        self._send_dl_msg(DlCodes.CAN_PROCEED_DL, idx)

        # TODO timeout?
        response = self.msg_queue.get(block=True)

        if response.code != DlCodes.DL_PERMISSION:
            # TODO send another msg ?
            print('in can proceed recvd unexpected msg', response)
            exit(1)

        return response.data

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
        print('[PIPED] dl error')

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
                os._exit(0)  # TODO maybe use another exit method
            else:
                self.msg_queue.put(msg)

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
