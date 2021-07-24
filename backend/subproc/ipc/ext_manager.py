from typing import List
import urllib.parse as parse
from backend.controller.observers.playlist_fetched_observer import PlaylistFetchedObserver
from backend.subproc.ipc.ipc_codes import ExtCodes
from backend.subproc.ipc.message import Message, Messenger
from backend.model.db_models import Playlist
import multiprocessing as mp
from multiprocessing.connection import Connection
from subproc.ext_server import run_server
from backend.subproc.ipc.subproc_lifetime_observer import SubprocLifetimeObserver
from backend.controller.gui.app_closed_observer import AppClosedObserver


class ExtManager(AppClosedObserver):
    def __init__(self, msger: Messenger):
        self.msger = msger

        self.pl_fetched_obss: List[PlaylistFetchedObserver] = []
        self.subproc_obss: List[SubprocLifetimeObserver] = []

        self.msg_handlers = {
            ExtCodes.PLAYLIST_FETCHED: self._on_playlist_fetched,
            ExtCodes.CONNECTION_NOT_ESTB: self._on_conn_not_estb,
            ExtCodes.LOST_CONNECTION: self._on_conn_lost,
        }

    def start(self):
        self.ext_conn, child_conn = mp.Pipe(duplex=True)
        self.ext_proc = mp.Process(target=run_server, args=(child_conn,))
        self.ext_proc.start()
        child_conn.close()

        for obs in self.subproc_obss:
            obs.on_subproc_created(self.ext_proc, self.ext_conn)

    def add_playlist_fetched_observer(self, obs: PlaylistFetchedObserver):
        self.pl_fetched_obss.append(obs)

    def add_subproc_lifetime_observer(self, obs: SubprocLifetimeObserver):
        self.subproc_obss.append(obs)

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
        # TODO check if all was fetched
        playlist_id = msg.data['echo']['data']['db_id']
        links_data = msg.data['links']

        playlist_idxs = [(self._get_playlist_idx(item['link']), i)
                         for i, item in enumerate(links_data)]

        playlist_idxs.sort(key=lambda x: x[0])
        sorted_ldata = [links_data[el[1]] for el in playlist_idxs]

        links, titles, data_links = ([item[key] for item in sorted_ldata]
                                     for key in ['link', 'title', 'dataLinks'])
        playlist_idxs = [x[0] for x in playlist_idxs]

        for obs in self.pl_fetched_obss:
            obs.on_playlist_fetched(
                playlist_id, playlist_idxs, links, titles, data_links)

    def _on_conn_lost(self, msg: Message):
        still_alive = msg.data
        if still_alive == 0:
            # TODO
            print('LOST ALL WS CONNECTIONS')

    def _on_conn_not_estb(self, msg: Message):
        # TODO
        print('RCVD TASK BUT CONNECTION NOT ESTB')

    def _get_playlist_idx(self, url: str):
        query = parse.urlparse(url).query
        return int(parse.parse_qs(query)['index'][0])

    def on_app_closed(self):
        self.msger.send(self.ext_conn, Message(ExtCodes.TERMINATE))
        for obs in self.subproc_obss:
            obs.on_termination_requested(self.ext_proc, self.ext_conn)
