import sys
import logging
from typing import List
from PyQt5.QtWidgets import QApplication
from backend.controller.data_list_items_factory import DataListItemsFactory
from backend.controller.playlists_summary_ctl import PlaylistsSummaryController
from backend.db.playlist_repo import PlaylistRepo
from backend.model.account import Account
from backend.model.link_creator import LinkCreator
from backend.model.link_renewer import LinkRenewer
from backend.model.playlist_dl_supervisor import PlaylistDownloadSupervisor
from backend.model.playlist_links_fetcher import PlaylistLinksFetcher
from backend.model.speedo import Speedo
from backend.db.db_session import DBSession
from backend.controller.main_window_ctl import MainWindowController
from backend.subproc.ipc.ipc_manager import IPCManager


class App(QApplication):
    def __init__(self, argv: List[str], sql_debug: bool = True):
        super().__init__(argv)

        self._setup_data_access_layer(sql_debug)

        self._setup_ipc_layer()

        self._setup_data_management_layer()

        for obs in [self.ipc_manager, self.speedo, self.playlist_dl_supervisor, self.link_creator]:
            self.main_window_ctl.add_app_closed_observer(obs)

    def _setup_data_access_layer(self, sql_debug):
        logging.info('setting up data access layer')
        self.db = DBSession(verbose=sql_debug)
        self.db.connect()

        self.repo = PlaylistRepo(self.db)
        self.account = Account(self.repo)

    def _setup_ipc_layer(self):
        logging.info('setting up ipc layer')
        self.ipc_manager = IPCManager()
        self.link_renewer = LinkRenewer(self.ipc_manager, self.repo)
        self.link_creator = LinkCreator(self.repo)

    def _setup_data_management_layer(self):
        logging.info('setting up data management layer')
        self.speedo = Speedo()

        self.playlist_fetcher = PlaylistLinksFetcher(
            self.account, self.repo, self.link_creator, self.ipc_manager)

        self.main_window_ctl = MainWindowController(
            self.repo, self.account, self.playlist_fetcher)

        self.playlist_dl_supervisor = PlaylistDownloadSupervisor(
            self.repo, self.account, self.link_renewer, self.ipc_manager, self.speedo)

        self.playlist_summary_ctl = PlaylistsSummaryController(
            self.account, self.main_window_ctl, DataListItemsFactory(), self.playlist_dl_supervisor)

        self.link_creator.add_link_created_observer(
            self.playlist_dl_supervisor)

        self.main_window_ctl.add_view_changed_observer(
            self.playlist_summary_ctl)

        self.ipc_manager.add_link_fetched_observer(self.link_renewer)
        self.ipc_manager.add_playlist_fetched_observer(self.playlist_fetcher)

    def run(self):
        logging.info('starting GUI')
        self.main_window_ctl.show(
            self.playlist_summary_ctl.get_data_summary_view())

    def stop(self):
        sys.exit(self.exec())


def main():
    logger_format = '[%(filename)s:%(lineno)d] %(levelname)-8s %(message)s'
    logging.basicConfig(level=logging.INFO, format=logger_format)
    app = App(sys.argv, sql_debug=False)
    app.run()  # blocking on main window
    app.stop()


if __name__ == '__main__':
    main()
