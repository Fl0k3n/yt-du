import asyncio
import websockets
import json
import os
from pathlib import Path
from utils.assets_loader import AssetsLoader as AL
from collections import deque
from backend.subproc.ipc.ipc_codes import ExtCodes
from backend.subproc.ipc.message import Message, Messenger
from multiprocessing.connection import Connection
import subprocess
import threading

PLAYLIST_FAILED_CODE = 1
PLAYLIST_SUCCEEDED_CODE = 2
DOWNLOADER_SCRIPT_NAME = 'yt_dl.py'
PORT = 5555


playlist = "https://www.youtube.com/watch?v=opgO6h9FIxA&list=PLtjUk3SyYzL5RTjUjk47FH6nCzBo69MMX"
playlist2 = "https://www.youtube.com/watch?v=IlQlKiPgBNk&list=PLmIOcjWlMZTL4qMZGua0xwXbRSSBu-m2r"
playlists = {'playlists': [playlist]}
# playlists = {'playlists': [playlist, playlist2]}
playlist_dir = {
    playlist: 'Gothic_playlist',
    playlist2: 'Stronghold_playlist'
}


def on_links_rcvd(playlist, links):
    playlist_path = Path(__file__).parent.joinpath(playlist_dir[playlist])
    try:
        os.mkdir(playlist_path)
    except FileExistsError as e:
        print(
            f'For playlist {playlist} directory at {playlist_path} already exists')
        # TODO check if all/what was downloaded

    for link_data in links:
        title = link_data['title']
        link = link_data['link']
        sub_link1, sub_link2 = link_data['dataLinks']

        if os.fork() == 0:
            os.execlp('python', DOWNLOADER_SCRIPT_NAME, DOWNLOADER_SCRIPT_NAME,
                      playlist, playlist_path, link, title, sub_link1, sub_link2)
        else:
            # TODO some data structure to add all pids
            # separate thread for waiting? or even this thing in separate thread or even process
            pid, status = os.wait()


def on_msg_rcvd(data):
    playlist = data['playlist']
    code = data['code']

    if code == PLAYLIST_SUCCEEDED_CODE:
        on_links_rcvd(playlist, data['data'])
    else:
        print("ERRRS")
        print(f"FOR Playlist {data['playlist']} got code: {data['code']}")
    # at playlist name (given)
    # create directory
    # for each link spawn worker and download
    # wait for all to finish and run next playlist
    # let every child log progress
    # in case of errors log in file that this item has failed


class ExtServer:
    def __init__(self, owner: Connection):
        self.owner = owner

        self.is_connected = False

        self.PORT, self.ADDRESS, self.BROWSER_PATH = [
            AL.get_env(val) for val in ['WS_PORT', 'WS_HOST', 'BROWSER']]

        self.server = websockets.serve(
            self._on_connected, self.ADDRESS, self.PORT, )

        self.tasks = deque()
        self.msger = Messenger()

        self.tasks_mutex = threading.Lock()
        self.connection_mutex = threading.Lock()

        self.task_added = threading.Condition(self.tasks_mutex)

    def run(self):
        print(f'WS server running at {self.ADDRESS}:{self.PORT}')
        self.listener = threading.Thread(
            target=self._listen_for_tasks, daemon=True)
        self.listener.start()
        asyncio.get_event_loop().run_until_complete(self.server)
        asyncio.get_event_loop().run_forever()

    def _listen_for_tasks(self):
        while True:
            msg = self.msger.recv(self.owner)
            # TODO handle different codes
            with self.tasks_mutex:
                self.tasks.append(msg)
                self.task_added.notify_all()

            with self.connection_mutex:
                if not self.is_connected:
                    # task rcvd but no connection, spawn browser
                    # subprocess.run([self.BROWSER_PATH])
                    print('TASK RCVD BUT NO CONNECTION')

    def _wait_for_task(self):
        with self.tasks_mutex:
            while not self.tasks:
                self.task_added.wait()

            return self.tasks[0]

    async def _get_task(self):
        # if nothing was queued wait for it non blocking
        loop = asyncio.get_running_loop()
        task = await loop.run_in_executor(None,
                                          self._wait_for_task)
        return task

    async def _on_connected(self, ws, path):
        print('-----------------------WS Connected-----------------')
        with self.connection_mutex:
            self.is_connected = True
        while True:
            task = await self._get_task()
            if task.code == ExtCodes.FETCH_PLAYLIST:
                await ws.send(task.to_json())
                resp = await ws.recv()
                self._on_ext_msg_rcvd(resp, ws)
            else:
                print('prrrrrrrrr', task)

            with self.tasks_mutex:
                self.tasks.popleft()

    def _on_ext_msg_rcvd(self, json_msg, ws):
        msg = Message.from_json(ExtCodes, json_msg)
        self.msger.send(self.owner, msg)


def run_server(conn):
    server = ExtServer(conn)
    server.run()


if __name__ == '__main__':
    run_server(None)
