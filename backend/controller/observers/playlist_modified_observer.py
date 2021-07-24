from abc import ABC, abstractmethod
from typing import Iterable
from backend.model.db_models import Playlist, PlaylistLink


class PlaylistModifiedObserver(ABC):
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
