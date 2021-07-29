from typing import List
from backend.model.db_models import Base, DataLink, Playlist, PlaylistLink
from backend.utils.assets_loader import AssetsLoader as AL
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from backend.controller.gui.app_closed_observer import AppClosedObserver


class DBHandler(AppClosedObserver):
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.engine = None
        self.session = None

    def connect(self):
        username, password, address, name = [
            AL.get_env('DB_' + x) for x in ['USERNAME', 'PASSWORD', 'ADDRESS', 'NAME']]

        self.engine = create_engine(
            f'postgresql+psycopg2://{username}:{password}@{address}/{name}',
            echo=self.verbose, future=True)

        Base.metadata.create_all(self.engine)

        self.session = Session(self.engine)

    def add_playlist(self, playlist: Playlist):
        self.session.add(playlist)

    def get_playlist(self, url: str = None, id: int = None) -> Playlist:
        q = self.session.query(Playlist)
        if id is not None:
            q = q.filter(Playlist.playlist_id == id)
        if url is not None:
            q = q.filter(Playlist.url == url)

        return q.first()

    def get_playlists(self, offset: int, limit: int) -> List[Playlist]:
        return (self.session
                .query(Playlist)
                .order_by(Playlist.added_at.desc())
                .offset(offset)
                .limit(limit))

    def get_playlist_count(self) -> int:
        return self.session.query(Playlist).count()

    def add_pl_link(self, pl_link: PlaylistLink):
        self.session.add(pl_link)

    def add_data_link(self, data_link: DataLink):
        self.session.add(data_link)

    def commit(self):
        self.session.commit()

    def on_app_closed(self):
        self.session.commit()
        self.session.close()
