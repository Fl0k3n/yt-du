from backend.controller.observers.link_fetched_observer import LinkFetchedObserver
from typing import Any, Dict, List
import urllib.parse as parse
from backend.controller.observers.playlist_fetched_observer import PlaylistFetchedObserver
from backend.model.playlist import Playlist
from backend.model.playlist_link import PlaylistLink
from backend.subproc.ipc.ipc_codes import ExtCodes
from backend.subproc.ipc.message import Message, Messenger
import multiprocessing as mp
from backend.subproc.ext_server import run_server
from backend.subproc.ipc.subproc_lifetime_observer import SubprocLifetimeObserver
from backend.controller.gui.app_closed_observer import AppClosedObserver
import threading


class ExtManager(AppClosedObserver):
    def __init__(self, msger: Messenger):
        self.msger = msger

        self.pl_fetched_obss: List[PlaylistFetchedObserver] = []
        self.link_fetched_obss: List[LinkFetchedObserver] = []
        self.subproc_obss: List[SubprocLifetimeObserver] = []

        # url -> original link
        self.fetch_link_queries: Dict[str, PlaylistLink] = {}

        self.msg_handlers = {
            ExtCodes.PLAYLIST_FETCHED: self._on_playlist_fetched,
            ExtCodes.CONNECTION_NOT_ESTB: self._on_conn_not_estb,
            ExtCodes.LOST_CONNECTION: self._on_conn_lost,
            ExtCodes.LINK_FETCHED: self._on_link_fetched,
        }

        self.last_query_id = -1
        # for renew requests url -> id of query
        self.blocking_link_queries: Dict[str, int] = {}
        # query id -> whatever response was
        self.blocking_link_responses: Dict[int, Any] = {}
        self.link_fetch_lock = threading.Lock()
        self.link_fetched_cond = threading.Condition(self.link_fetch_lock)

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

    def add_link_fetched_observer(self, obs: LinkFetchedObserver):
        self.link_fetched_obss.append(obs)

    def query_playlist_links(self, playlist: Playlist):
        ext_data = {
            'url': playlist.get_url(),
            'db_id': playlist.get_playlist_id()
        }

        msg = Message(ExtCodes.FETCH_PLAYLIST, ext_data)
        self.msger.send(self.ext_conn, msg)

    def query_link(self, playlist_link: PlaylistLink):
        ext_data = {
            'url': playlist_link.get_url()
        }

        self.fetch_link_queries[playlist_link.get_url()] = playlist_link

        msg = Message(ExtCodes.FETCH_LINK, ext_data)
        self.msger.send(self.ext_conn, msg)

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

    def _on_link_fetched(self, msg: Message):
        data = msg.data
        link = data['link']
        data_links = data['dataLinks']
        print('got links', data_links)

        with self.link_fetch_lock:
            if link in self.blocking_link_queries:
                q_id = self.blocking_link_queries.pop(link)
                self.blocking_link_responses[q_id] = data_links
                self.link_fetched_cond.notify_all()
            else:
                playlist_link = self.fetch_link_queries.pop(link)
                for obs in self.link_fetched_obss:
                    obs.on_link_fetched(playlist_link, data_links)

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

    def query_link_blocking(self, playlist_link: PlaylistLink) -> List[str]:
        ext_data = {
            'url': playlist_link.get_url()
        }
        with self.link_fetch_lock:
            self.last_query_id += 1
            q_id = self.last_query_id
            self.blocking_link_queries[playlist_link.get_url()] = q_id

        msg = Message(ExtCodes.FETCH_LINK, ext_data)
        self.msger.send(self.ext_conn, msg)

        with self.link_fetch_lock:
            while q_id not in self.blocking_link_responses:
                self.link_fetched_cond.wait()

            return self.blocking_link_responses.pop(q_id)
