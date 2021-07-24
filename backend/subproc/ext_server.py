import asyncio
import websockets
from utils.assets_loader import AssetsLoader as AL
from collections import deque
from backend.subproc.ipc.ipc_codes import ExtCodes
from backend.subproc.ipc.message import Message, Messenger
from multiprocessing.connection import Connection
import threading
import signal
import os


class ExtServer:
    def __init__(self, owner: Connection):
        self.owner = owner

        self.connections = set()

        self.PORT, self.ADDRESS, self.BROWSER_PATH = [
            AL.get_env(val) for val in ['WS_PORT', 'WS_HOST', 'BROWSER']]

        self.server = websockets.serve(
            self._on_connected, self.ADDRESS, self.PORT)

        self.tasks = deque()
        self.msger = Messenger()

        self.tasks_mutex = threading.Lock()
        self.connection_mutex = threading.Lock()
        self.msger_mutex = threading.Lock()

        self.task_added = threading.Condition(self.tasks_mutex)

    async def _server(self, stop):
        async with self.server:
            await stop

    def run(self):
        print(f'WS server running at {self.ADDRESS}:{self.PORT}')
        self.listener = threading.Thread(
            target=self._listen_for_tasks, daemon=True)
        self.listener.start()

        loop = asyncio.get_event_loop()
        stop = loop.create_future()
        loop.add_signal_handler(signal.SIGINT, stop.set_result, None)

        loop.run_until_complete(self._server(stop))

    def _listen_for_tasks(self):
        # TODO doesnt work with sigmask, without sigmask race condition possible
        # signal.pthread_sigmask(signal.SIG_BLOCK, [signal.SIGINT])

        while True:
            msg = self.msger.recv(self.owner)
            if msg.code == ExtCodes.TERMINATE:
                signal.raise_signal(signal.SIGINT)
                return

            with self.tasks_mutex:
                self.tasks.append(msg)
                self.task_added.notify_all()

            with self.connection_mutex:
                if not self.connections:
                    self._send_msg(Message(
                        ExtCodes.CONNECTION_NOT_ESTB))

    def _wait_for_task(self):
        with self.tasks_mutex:
            while not self.tasks:
                self.task_added.wait()

            return self.tasks[0]

    async def _get_task(self):
        # if nothing was queued wait for it non blocking
        with self.tasks_mutex:
            if self.tasks:
                return self.tasks[0]

        loop = asyncio.get_running_loop()
        task = await loop.run_in_executor(None,
                                          self._wait_for_task)
        return task

    async def _on_connected(self, ws, path):
        print('-----------------------WS Connected-----------------')
        with self.connection_mutex:
            self.connections.add(ws)
        while True:
            # TODO keeps process alive, SIGKILL required
            task = await self._get_task()
            if task.code == ExtCodes.FETCH_PLAYLIST:
                try:
                    await ws.send(task.to_json())
                    resp = await ws.recv()

                    self._on_ext_msg_rcvd(resp, ws)

                    with self.tasks_mutex:
                        self.tasks.popleft()
                except websockets.ConnectionClosed:
                    with self.connection_mutex:
                        self.connections.remove(ws)
                        self._send_msg(
                            Message(ExtCodes.LOST_CONNECTION, len(self.connections)))
                    return
            else:
                print('prrrrrrrrr', task)
                raise RuntimeError('Unexpected task code')  # TODO

    def _on_ext_msg_rcvd(self, json_msg, ws):
        msg = Message.from_json(ExtCodes, json_msg)
        self._send_msg(msg)

    def _send_msg(self, msg: Message):
        with self.msger_mutex:
            self.msger.send(self.owner, msg)


def run_server(conn):
    server = ExtServer(conn)
    server.run()


if __name__ == '__main__':
    run_server(None)
