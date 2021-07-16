from model.db_models import Base, Playlist
from utils.assets_loader import AssetsLoader as AL
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session


class DBHandler:
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
        self.session.commit()

    def get_playlist(self, url: str) -> Playlist:
        return self.session.query(Playlist).filter(Playlist.url == url).one_or_none()
