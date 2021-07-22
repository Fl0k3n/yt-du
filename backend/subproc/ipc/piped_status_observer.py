from typing import Any
from backend.subproc.yt_dl import StatusObserver
from backend.subproc.ipc.message import Message, Messenger, DlData
from backend.subproc.ipc.ipc_codes import DlCodes
from multiprocessing.connection import Connection


class PipedStatusObserver(StatusObserver):
    def __init__(self, conn: Connection, task_id: int, msger: Messenger):
        self.msger = msger
        self.task_id = task_id
        self.conn = conn

    def dl_started(self, idx: int):
        msg = self._create_dl_msg(DlCodes.DL_STARTED, idx)
        self.msger.send(self.conn, msg)

    def dl_finished(self, idx: int):
        print('[PIPED] dl finished')

    def chunk_fetched(self, idx: int, bytes_len: int):
        msg = self._create_dl_msg(DlCodes.CHUNK_FETCHED, (idx, bytes_len))
        self.msger.send(self.conn, msg)

    def can_proceed_dl(self, idx: int) -> bool:
        msg = self._create_dl_msg(DlCodes.CAN_PROCEED_DL, idx)
        self.msger.send(self.conn, msg)
        # TODO timeout?
        response = self.msger.recv(self.conn)

        if response.code != DlCodes.DL_PERMISSION:
            # TODO send another msg ?
            print('in can proceed recvd unexpected msg', response)
            exit(1)

        return response.data

    def merge_started(self):
        print('[PIPED] merge started')

    def merge_finished(self, status: int, stderr: str):
        print('[PIPED] merge finished')

    def dl_error_occured(self, idx: int, exc_type: str, exc_msg: str):
        print('[PIPED] dl error')

    def process_finished(self, success: bool):
        print('[PIPED] proc finished')

    def _create_dl_msg(self, code: DlCodes, data: Any) -> DlData:
        return Message(code, DlData(self.task_id, data))
