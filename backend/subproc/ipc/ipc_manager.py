import multiprocessing as mp
from multiprocessing.connection import Connection, wait
from typing import List
from backend.model.db_models import Playlist
from subproc.ext_server import run_server
from subproc.ipc.message import Message, Messenger
from subproc.ipc.ipc_codes import ExtCodes
from PyQt5.QtCore import QObject, QThread, pyqtSignal


class IPCListener(QObject):
    msg_rcvd = pyqtSignal(Message)
    finished = pyqtSignal()

    def __init__(self, connections: List[Connection], msger: Messenger):
        super().__init__()
        self.connections = connections
        self.msger = msger
        self.keep_listening = True

    def add_connection(self, connection: Connection):
        self.connections.append(connection)

    def remove_connection(self, connection: Connection):
        self.connections.remove(connection)

    def stop(self):
        self.keep_listening = False

    def run(self):
        while self.keep_listening and self.connections:
            print('looping')
            for rdy_con in wait(self.connections):
                try:
                    msg = self.msger.recv(rdy_con)
                    self.msg_rcvd.emit(msg)
                except EOFError:
                    self.remove_connection(rdy_con)
                    # TODO

        self.finished.emit()
        # TODO
        raise RuntimeError('LISTENER FINISHED!!!')


class IPCManager:
    def __init__(self):
        # spawn ws server
        # server is listennig for queries
        self.msger = Messenger()
        self.children = []

        self._spawn_extension_worker()
        self._create_listener_thread()

    def _create_listener_thread(self):
        self.listener_thread = QThread()

        self.listener = IPCListener([self.ext_conn], self.msger)
        self.listener.moveToThread(self.listener_thread)
        self.listener.msg_rcvd.connect(self._on_msg_rcvd)
        self.listener.finished.connect(
            lambda: print('handle listener finish'))

        self.listener_thread.started.connect(self.listener.run)
        self.listener_thread.start()

    def _on_msg_rcvd(self, msg: Message):
        print('MANAGER GOT')
        print(msg)

    def _spawn_extension_worker(self):
        self.ext_conn, child_conn = mp.Pipe(duplex=True)
        self.ext_proc = mp.Process(target=run_server, args=(child_conn,))
        self.ext_proc.start()
        self.children.append(self.ext_proc)
        child_conn.close()

    def query_playlist_links(self, playlist: Playlist):
        # send url to ws server
        # go to listennig for data links state
        msg = Message(ExtCodes.FETCH_PLAYLIST, playlist.url)
        self.msger.send(self.ext_conn, msg)
        print('sent')

    def on_links_rcvd(self):
        # contact playlist mgr
        # mark it as rcvd
        # ? start dl'ing ???
        pass

    def start_dl(self, args):
        # spawn yt_dl proc
        # give it args neccesary to dl single link
        # setup listeners for communication with it
        pass

    def on_dl_msg(self):
        # figure out which link
        # figure out if error or smth
        # contact observers that dl proceeded
        # if done do non-blocking os.wait
        pass

    def stop(self):
        # TODO
        print('terminating children.')
        for child in self.children:
            if child.is_alive():
                child.terminate()
            child.join()
