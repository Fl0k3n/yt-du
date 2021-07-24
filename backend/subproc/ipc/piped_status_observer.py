from typing import Any
from backend.subproc.yt_dl import StatusObserver
from backend.subproc.ipc.message import Message, Messenger, DlData
from backend.subproc.ipc.ipc_codes import DlCodes
from multiprocessing.connection import Connection
from threading import Lock


class PipedStatusObserver(StatusObserver):
    def __init__(self, conn: Connection, task_id: int, msger: Messenger):
        self.msger = msger
        self.task_id = task_id
        self.conn = conn
        self.msger_lock = Lock()

    def dl_started(self, idx: int):
        self._send_dl_msg(DlCodes.DL_STARTED, idx)

    def dl_finished(self, idx: int):
        self._send_dl_msg(DlCodes.DL_FINISHED, idx)

    def chunk_fetched(self, idx: int, bytes_len: int):
        self._send_dl_msg(DlCodes.CHUNK_FETCHED, (idx, bytes_len))

    def can_proceed_dl(self, idx: int) -> bool:
        self._send_dl_msg(DlCodes.CAN_PROCEED_DL, idx)

        # TODO timeout?
        with self.msger_lock:
            response = self.msger.recv(self.conn)

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
        with self.msger_lock:
            self.msger.send(self.conn, msg)
