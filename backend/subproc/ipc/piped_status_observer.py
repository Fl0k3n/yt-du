from backend.subproc.yt_dl import StatusObserver
from backend.subproc.ipc.message import Message, Messenger
from multiprocessing.connection import Connection


class PipedStatusObserver(StatusObserver):
    def __init__(self, conn: Connection, msger: Messenger):
        self.msger = msger
        self.conn = conn

    def dl_started(self, url: str):
        print('[PIPED] dl started')

    def dl_finished(self, url: str):
        print('[PIPED] dl finished')

    def chunk_fetched(self, url: str, bytes_len: int):
        print('[PIPED] chunk fetched')

    def can_proceed_dl(self, url: str) -> bool:
        print('[PIPED] can proceed')
        return True

    def merge_started(self):
        print('[PIPED] merge started')

    def merge_finished(self, status: int, stderr: str):
        print('[PIPED] merge finished')

    def dl_error_occured(self, exc_type: str, exc_msg: str):
        print('[PIPED] dl error')

    def process_finished(self, success: bool):
        print('[PIPED] proc finished')
