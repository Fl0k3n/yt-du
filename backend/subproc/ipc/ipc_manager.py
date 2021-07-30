from backend.subproc.yt_dl import MediaURL
from backend.subproc.ipc.link_renewed_observer import LinkRenewedObserver
from backend.controller.observers.link_fetched_observer import LinkFetchedObserver
import time
import threading
import multiprocessing as mp
from backend.subproc.ipc.subproc_lifetime_observer import SubprocLifetimeObserver
from backend.controller.gui.app_closed_observer import AppClosedObserver
from backend.model.dl_task import DlTask
from backend.controller.observers.playlist_fetched_observer import PlaylistFetchedObserver
from backend.subproc.ipc.ipc_codes import ExtCodes, DlCodes
from multiprocessing.connection import Connection, wait
from typing import Dict, List, Set
from backend.model.db_models import Playlist, PlaylistLink
from backend.subproc.ipc.message import Message, Messenger
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QWaitCondition, QMutex
from backend.subproc.ipc.ext_manager import ExtManager
from backend.subproc.ipc.dl_manager import DlManager


class IPCListener(QObject):
    msg_rcvd = pyqtSignal(Message)
    conn_closed = pyqtSignal(Connection)

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
        self.keep_listening = False
        self.wake_up_w.send('')

    def run(self):
        while self.keep_listening:
            self.conn_mutex.lock()
            while not self.connections:
                self.conn_not_empty.wait(self.conn_mutex)

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
                    rdy_con.close()
                    self.conn_closed.emit(rdy_con)

            self.conn_mutex.unlock()


class IPCManager(SubprocLifetimeObserver, AppClosedObserver, LinkRenewedObserver):
    # if after this #seconds child is still alive, it will rcv SIGKILL (or mp equivalent)
    _KILL_CHILDREN_TIMEOUT = 1
    # non blocking join is issued after this #seconds
    _JOIN_CHILDREN_TIMEOUT = 1

    def __init__(self):
        self.msger = Messenger()
        self.children: Set[mp.Process] = set()
        self.conn_to_child: Dict[Connection, mp.Process] = {}

        self._create_listener_thread()

        self.ext_manager = ExtManager(self.msger)
        self.dl_manager = DlManager(self.msger)

        self.ext_codes = set(ExtCodes)
        self.dl_codes = set(DlCodes)

        for mgr in (self.ext_manager, self.dl_manager):
            mgr.add_subproc_lifetime_observer(self)

        self.ext_manager.start()

        self.app_closed_observers: List[AppClosedObserver] = [
            self.ext_manager, self.dl_manager]

        # if connection is in this set subprocess exits as expected
        # info from listener about losing such connection
        # should be ignored
        self.expected_dead_connections: Set[Connection] = set()

    def _create_listener_thread(self):
        self.listener_thread = QThread()

        self.listener = IPCListener(self.msger)
        self.listener.moveToThread(self.listener_thread)
        self.listener.msg_rcvd.connect(self._on_msg_rcvd)
        self.listener.conn_closed.connect(self._on_conn_closed)

        self.listener_thread.started.connect(self.listener.run)
        self.listener_thread.start()

    def add_playlist_fetched_observer(self, obs: PlaylistFetchedObserver):
        self.ext_manager.add_playlist_fetched_observer(obs)

    def add_link_fetched_observer(self, obs: LinkFetchedObserver):
        self.ext_manager.add_link_fetched_observer(obs)

    def _on_msg_rcvd(self, msg: Message):
        print(f'MANAGER GOT [{msg.code}]')
        if msg.code in self.ext_codes:
            self.ext_manager.msg_rcvd(msg)
        elif msg.code in self.dl_codes:
            self.dl_manager.msg_rcvd(msg)
        else:
            raise AttributeError(f'Unexpected IPC code msg: {msg}')

    def _on_conn_closed(self, conn: Connection):
        # this is called when listener detects broken pipe
        if conn in self.expected_dead_connections:
            self.expected_dead_connections.remove(conn)
        else:
            print('UNEXPECTED DEAD CONNECTION')
            self.conn_to_child[conn].join()

        self.conn_to_child.pop(conn)

    def query_playlist_links(self, playlist: Playlist):
        self.ext_manager.query_playlist_links(playlist)

    def query_link(self, playlist_link: PlaylistLink):
        self.ext_manager.query_link(playlist_link)

    def query_link_blocking(self, playlist_link: PlaylistLink) -> List[str]:
        return self.ext_manager.query_link_blocking(playlist_link)

    def schedule_dl_task(self, task: DlTask) -> int:
        return self.dl_manager.schedule_task(task)

    def on_subproc_created(self, process: mp.Process, con: Connection):
        self.listener.add_connection(con)
        self.conn_to_child[con] = process
        self.children.add(process)

    def on_subproc_finished(self, process: mp.Process, con: Connection):
        # this is called when process finishes as expected
        self.children.remove(process)
        self.expected_dead_connections.add(con)

        # conn will be removed on broken pipe
        print('Joining process')
        process.join()
        print('Joined')

    def on_app_closed(self):
        for obs in self.app_closed_observers:
            obs.on_app_closed()

        self.listener.stop()
        # schedule killer thread

        def kill_em_all():
            time.sleep(self._JOIN_CHILDREN_TIMEOUT)
            print('JOINING')
            to_rm = set()
            for proc in self.children:
                if not proc.is_alive():
                    proc.join()
                    to_rm.add(proc)

            self.children = self.children.difference(to_rm)
            if not self.children:
                print('ALL JOINED')
                return

            time.sleep(self._KILL_CHILDREN_TIMEOUT)
            print('TERMINATING')
            for proc in self.children:
                if proc.is_alive():
                    print('CHILD IS STILL ALIVE')
                    proc.terminate()
                proc.join()

        threading.Thread(target=kill_em_all).start()

    def on_termination_requested(self, process: mp.Process, con: Connection):
        # this is called after TERMINATE msg was sent
        self.expected_dead_connections.add(con)

    def pause_dl(self, task_id: int) -> bool:
        """returns True if task was running """
        return self.dl_manager.pause_task(task_id)

    def on_link_renewed(self, task_id: int, link_idx: int, renewed: MediaURL, is_consistent: bool):
        self.dl_manager.on_link_renewed(
            task_id, link_idx, renewed, is_consistent)
