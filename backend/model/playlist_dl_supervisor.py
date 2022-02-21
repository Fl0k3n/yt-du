import datetime
from backend.controller.app_closed_observer import AppClosedObserver
from backend.model.link_created_observer import LinkCreatedObserver
from backend.model.link_renewer import LinkRenewer
from backend.model.playlist_dl_manager import PlaylistDlManager
from backend.model.speedo import Speedo
from backend.db.playlist_repo import PlaylistRepo
from backend.model.account import Account
from backend.model.data_link import DataLink
from backend.model.data_status import DataStatus
from backend.model.playlist import Playlist
from backend.model.playlist_link import PlaylistLink
from backend.model.playlist_link_task import PlaylistLinkTask
from backend.subproc.ipc.ipc_manager import IPCManager
from backend.subproc.pl_link_resumer import PlaylistLinkResumer


class PlaylistDownloadSupervisor(PlaylistDlManager, LinkCreatedObserver, AppClosedObserver):

    def __init__(self, repo: PlaylistRepo, account: Account, link_renerwer: LinkRenewer,
                 ipc_mgr: IPCManager, speedo: Speedo):
        self.repo = repo
        self.account = account
        self.link_renewer = link_renerwer
        self.ipc_mgr = ipc_mgr
        self.speedo = speedo

    def on_link_created(self, playlist_link: PlaylistLink, data_link: DataLink, playlist_rdy: bool):
        if playlist_rdy:
            playlist = playlist_link.get_playlist()

            for pl_link in playlist.get_playlist_links():
                task = self._create_task(pl_link)
                task_id = self.ipc_mgr.schedule_dl_task(task)
                pl_link.set_dl_task_id(task_id)

    def on_process_started(self, playlist_link: PlaylistLink, tmp_files_dir: str):
        print('DL PROCESS STARTED FOR ', playlist_link.get_name())
        playlist_link.set_tmp_files_dir_path(tmp_files_dir)

        if playlist_link.is_resume_requested():
            playlist_link.set_resume_requested(False)

        if playlist_link.get_playlist().is_resume_requested():
            playlist_link.get_playlist().set_resume_requested(False)

        self.repo.update()

    def on_dl_started(self, playlist_link: PlaylistLink, data_link: DataLink, abs_path: str):
        playlist = playlist_link.get_playlist()
        first_link = False
        first_data_link = False

        if playlist_link.get_status() != DataStatus.DOWNLOADING:
            playlist_link.set_link_dling_count(1)
            playlist_link.set_status(DataStatus.DOWNLOADING)
            self.link_renewer.set_consistent(playlist_link, True)
            first_data_link = True
        else:
            playlist_link.set_link_dling_count(
                playlist_link.get_link_dling_count() + 1)

        # wont be called if count drops to 0 then gets resumed
        if first_data_link:
            if playlist.get_status() != DataStatus.DOWNLOADING:
                playlist.set_dling_count(1)
                playlist.set_status(DataStatus.DOWNLOADING)
                first_link = True
            else:
                playlist.set_dling_count(playlist.get_dling_count() + 1)

        data_link.set_dl_start_time(datetime.datetime.now())
        data_link.set_path(abs_path)
        self.repo.update()

        if first_data_link:
            print('DL STARTED for ', playlist_link.get_name())

        if first_link or playlist.get_dling_count() == 1:
            self.speedo.dl_resumed(playlist)

    def can_proceed_dl(self, playlist_link: PlaylistLink, data_link: DataLink) -> bool:
        return not playlist_link.is_pause_requested() and \
            self.link_renewer.is_consistent(playlist_link)

    def on_dl_progress(self, playlist_link: PlaylistLink,
                       data_link: DataLink, expected_bytes_to_fetch: int,
                       bytes_fetched: int, chunk_url: str):
        size_diff = bytes_fetched - expected_bytes_to_fetch

        data_link.set_size(data_link.get_size() + size_diff)
        data_link.set_dled_size(data_link.get_dled_size() + bytes_fetched)
        data_link.set_last_chunk_url(chunk_url)

        self.repo.update()

        self.speedo.dl_progressed(playlist_link.get_playlist(), bytes_fetched)

    def on_data_link_dled(self, playlist_link: PlaylistLink, data_link: DataLink):
        print(
            f'finished downloading {data_link.get_mime()} for {playlist_link.get_name()}')
        playlist_link.set_link_dling_count(
            playlist_link.get_link_dling_count() - 1)

    def on_link_dled(self, playlist_link: PlaylistLink):
        playlist = playlist_link.get_playlist()
        playlist.set_dling_count(playlist.get_dling_count() - 1)
        playlist_link.set_status(DataStatus.WAIT_FOR_MERGE)
        self.repo.update()

        if playlist.get_dling_count() == 0:
            self.speedo.dl_stopped(playlist)

    def on_merge_started(self, playlist_link: PlaylistLink):
        playlist_link.set_status(DataStatus.MERGING)
        self.repo.update()

    def on_merge_finished(self, playlist_link: PlaylistLink, status: int, stderr: str):
        # TODO
        if status != 0:
            playlist_link.set_status(DataStatus.ERRORS)
            self.repo.update()
            print(
                f'link {playlist_link.get_name()} | {playlist_link.get_url()} FAILED')
            print('*'*80)
            print(stderr)
            print('*'*80)

    def on_process_finished(self, playlist_link: PlaylistLink, success: bool):
        # TODO
        old_status = playlist_link.get_status()

        if not success and old_status == DataStatus.WAIT_FOR_MERGE:  # fail on dl stage
            # TODO
            print('Failed on dl stage, retrying')
            for dlink in playlist_link.get_data_links():
                dlink.set_dled_size(0)
                dlink.set_last_chunk_url(None)
                dlink.set_path(None)

            self.repo.update()
            task = self._create_task(playlist_link)
            task_id = self.ipc_mgr.schedule_dl_task(task)

            playlist_link.set_dl_task_id(task_id)
        else:
            # TODO handle failure on other stage
            playlist_link.set_status(DataStatus.FINISHED)
            playlist_link.set_cleaned_up(True)

            self.repo.update()

            playlist_link.set_dl_task_finished()
            playlist = playlist_link.get_playlist()

            if not self.link_renewer.is_consistent(playlist_link):
                self._handle_inconsistent(playlist_link)
            elif playlist.is_finished():
                playlist.set_status(DataStatus.FINISHED)
                self.repo.update()
            elif playlist.is_paused():
                playlist.set_status(DataStatus.PAUSED)
                self.repo.update()

    def _handle_inconsistent(self, playlist_link: PlaylistLink):
        # called when process downloading inconsistent link finishes
        playlist_link.set_tmp_files_dir_path(None)
        playlist_link.set_status(DataStatus.WAIT_FOR_DL)

        playlist_link.set_size(playlist_link.get_size_bytes())

        for dlink in playlist_link.data_links:
            dlink.set_dled_size(0)
            dlink.set_last_chunk_url(None)

        self.repo.update()

        task = self._create_task(playlist_link)
        task_id = self.ipc_mgr.schedule_dl_task(task)
        playlist_link.set_dl_task_id(task_id)

    def on_process_paused(self, playlist_link: PlaylistLink):
        playlist_link.set_dl_task_finished()
        playlist_link.set_link_dling_count(0)

        self._playlist_link_paused(playlist_link)

        playlist = playlist_link.playlist

        if playlist.is_paused():
            self.speedo.dl_stopped(playlist)

    def _playlist_link_paused(self, playlist_link: PlaylistLink):
        playlist_link.set_pause_requested(False)
        playlist_link.set_status(DataStatus.PAUSED)

        playlist = playlist_link.get_playlist()

        if playlist.is_paused():
            playlist.set_status(DataStatus.PAUSED)
            playlist.set_pause_requested(False)

        self.repo.update()

    def on_playlist_pause_requested(self, playlist: Playlist):
        playlist.set_pause_requested(True)

        for link in playlist.get_downloading_links():
            self.on_link_pause_requested(link)

    def on_link_pause_requested(self, playlist_link: PlaylistLink) -> bool:
        running = self.ipc_mgr.pause_dl(playlist_link.get_dl_task_id())
        playlist_link.set_pause_requested(True)

        if not running:
            self._playlist_link_paused(playlist_link)

        return running

    def on_link_resume_requested(self, playlist_link: PlaylistLink):
        self._resume_link(playlist_link)

    def on_playlist_resume_requested(self, playlist: Playlist):
        playlist.set_resume_requested(True)

        for link in playlist.get_playlist_links():
            if link.is_resumable():
                self._resume_link(link)

    def _resume_link(self, playlist_link: PlaylistLink):
        playlist_link.set_resume_requested(True)

        resumer = PlaylistLinkResumer(playlist_link)
        task = self._create_task(playlist_link)
        task.resume(resumer)

        task_id = self.ipc_mgr.schedule_dl_task(task)
        playlist_link.set_dl_task_id(task_id)

    def _create_task(self, playlist_link: PlaylistLink) -> PlaylistLinkTask:
        return PlaylistLinkTask(playlist_link, self, self.link_renewer)

    def on_app_closed(self):
        for playlist in self.account.get_playlists():
            playlist.force_pause()

        self.repo.update()
        # self.db.on_app_closed() TODO
