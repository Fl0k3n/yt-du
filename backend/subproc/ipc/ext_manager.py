from backend.controller.observers.playlist_fetched_observer import PlaylistFetchedObserver
from subproc.ipc.ipc_codes import ExtCodes
from backend.subproc.ipc.message import Message, Messenger
from backend.model.db_models import Playlist
import multiprocessing as mp
from multiprocessing.connection import Connection
from subproc.ext_server import run_server


class ExtManager:
    def __init__(self, msger: Messenger):
        self.msger = msger
        self.ext_conn, child_conn = mp.Pipe(duplex=True)
        self.ext_proc = mp.Process(target=run_server, args=(child_conn,))
        self.ext_proc.start()
        child_conn.close()

        self.pl_fetched_obss = []

        self.msg_handlers = {
            ExtCodes.PLAYLIST_FETCHED: self._on_playlist_fetched
        }

    def add_playlist_fetched_observer(self, obs: PlaylistFetchedObserver):
        self.pl_fetched_obss.append(obs)

    def get_connection(self) -> Connection:
        return self.ext_conn

    def get_subproc(self) -> mp.Process:
        return self.ext_proc

    def query_playlist_links(self, playlist: Playlist):
        ext_data = {
            'url': playlist.url,
            'db_id': playlist.playlist_id
        }

        msg = Message(ExtCodes.FETCH_PLAYLIST, ext_data)
        self.msger.send(self.ext_conn, msg)
        print('sent to server')

    def msg_rcvd(self, msg: Message):
        # will raise KeyError for wrong code
        self.msg_handlers[msg.code](msg)

    def _on_playlist_fetched(self, msg: Message):
        from pprint import pprint
        pprint(msg.data)
        playlist_id = msg.data['echo']['data']['db_id']
        links_data = msg.data['links']

        links, titles, data_links = ([item[key] for item in links_data]
                                     for key in ['link', 'title', 'dataLinks'])

        for obs in self.pl_fetched_obss:
            obs.on_playlist_fetched(playlist_id, links, titles, data_links)
