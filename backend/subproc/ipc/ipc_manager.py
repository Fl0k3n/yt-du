from backend.subproc.ipc.subproc_lifetime_observer import SubprocLifetimeObserver
from backend.model.dl_task import DlTask
from backend.controller.observers.playlist_fetched_observer import PlaylistFetchedObserver
from subproc.ipc.ipc_codes import ExtCodes
import multiprocessing as mp
from multiprocessing.connection import Connection, wait
from typing import List
from backend.model.db_models import Playlist
from subproc.ipc.message import Message, Messenger
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QWaitCondition, QMutex
from backend.subproc.ipc.ext_manager import ExtManager
from backend.subproc.ipc.dl_manager import DlManager


class IPCListener(QObject):
    msg_rcvd = pyqtSignal(Message)
    finished = pyqtSignal()

    def __init__(self, msger: Messenger, connections: List[Connection] = None):
        super().__init__()
        self.connections = connections if connections is not None else []
        self.msger = msger
        self.keep_listening = True

        self.wake_up_r, self.wake_up_w = mp.Pipe(duplex=False)
        self.conn_mutex = QMutex()
        self.conn_not_empty = QWaitCondition()

    def add_connection(self, connection: Connection):
        self.conn_mutex.lock()
        self.connections.append(connection)

        self.conn_not_empty.wakeAll()  # wake from cond wait
        self.wake_up_w.send('')  # wake from poll wait

        self.conn_mutex.unlock()

    def stop(self):
        # TODO wake here?
        self.keep_listening = False

    def run(self):
        while self.keep_listening:
            self.conn_mutex.lock()
            while not self.connections:
                self.conn_not_empty.wait(self.conn_mutex)

            print('looping')
            tmp = [self.wake_up_r, *self.connections]
            self.conn_mutex.unlock()
            rdy = wait(tmp)
            self.conn_mutex.lock()

            for rdy_con in rdy:
                if rdy_con == self.wake_up_r:
                    self.wake_up_r.recv()  # ignore it
                    continue
                try:
                    msg = self.msger.recv(rdy_con)
                    self.msg_rcvd.emit(msg)
                except EOFError:
                    self.connections.remove(rdy_con)
                    # TODO

            self.conn_mutex.unlock()

        self.finished.emit()
        # TODO
        raise RuntimeError('LISTENER FINISHED!!!')


class IPCManager(SubprocLifetimeObserver):
    def __init__(self):
        # spawn ws server
        # server is listennig for queries
        self.msger = Messenger()
        self.children: List[mp.Process] = []
        self._create_listener_thread()

        self.ext_manager = ExtManager(self.msger)
        self.dl_manager = DlManager(self.msger)

        for mgr in (self.ext_manager, self.dl_manager):
            mgr.add_subproc_lifetime_observer(self)

        self.ext_manager.start()

    def _create_listener_thread(self):
        self.listener_thread = QThread()

        self.listener = IPCListener(self.msger)
        self.listener.moveToThread(self.listener_thread)
        self.listener.msg_rcvd.connect(self._on_msg_rcvd)
        self.listener.finished.connect(
            lambda: print('handle listener finish'))

        self.listener_thread.started.connect(self.listener.run)
        self.listener_thread.start()

    def add_playlist_fetched_observer(self, obs: PlaylistFetchedObserver):
        self.ext_manager.add_playlist_fetched_observer(obs)

    def _on_msg_rcvd(self, msg: Message):
        print(f'MANAGER GOT [{msg.code}]')
        if msg.code in set(ExtCodes):
            self.ext_manager.msg_rcvd(msg)
        else:
            print('Unexpected code')

    def query_playlist_links(self, playlist: Playlist):
        self.ext_manager.query_playlist_links(playlist)

    def schedule_dl_task(self, task: DlTask):
        self.dl_manager.schedule_task(task)

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

    def on_subproc_created(self, process: mp.Process, con: Connection):
        self.listener.add_connection(con)
        self.children.append(process)