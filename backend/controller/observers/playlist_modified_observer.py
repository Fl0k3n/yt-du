from abc import ABC, abstractmethod
from backend.controller.observers.dl_speed_updated_observer import DlSpeedUpdatedObserver
from typing import Iterable
from backend.model.db_models import Playlist, PlaylistLink


class PlaylistModifiedObserver(DlSpeedUpdatedObserver, ABC):
    @abstractmethod
    def playlist_added(self, playlist: Playlist):
        pass

    @abstractmethod
    def playlist_links_added(self, playlist: Playlist):
        pass

    @abstractmethod
    def playlist_dl_started(self, playlist: Playlist):
        pass

    @abstractmethod
    def link_dl_started(self, playlist_link: PlaylistLink):
        pass

    @abstractmethod
    def playlist_dl_progressed(self, playlist: Playlist, playlist_link: PlaylistLink):
        pass

    @abstractmethod
    def playlist_link_dled(self, playlist_link: PlaylistLink):
        pass

    @abstractmethod
    def playlist_link_merging(self, playlist_link: PlaylistLink):
        pass

    @abstractmethod
    def playlist_link_finished(self, playlist_link: PlaylistLink):
        pass

    @abstractmethod
    def playlist_finished(self, playlist: Playlist):
        pass

    @abstractmethod
    def playlist_link_paused(self, playlist_link: PlaylistLink):
        pass

    @abstractmethod
    def playlist_paused(self, playlist: Playlist):
        pass

    @abstractmethod
    def playlist_link_pause_requested(self, playlist_link: PlaylistLink):
        pass

    @abstractmethod
    def playlist_pause_requested(self, playlist: Playlist):
        pass

    @abstractmethod
    def playlist_link_resume_requested(self, playlist_link: PlaylistLink):
        pass

    @abstractmethod
    def playlist_resume_requested(self, playlist: Playlist):
        pass
