from typing import List
from backend.model.db_models import Base, DB_DataLink, DB_Playlist, DB_PlaylistLink
from backend.utils.assets_loader import AssetsLoader as AL
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from backend.controller.gui.app_closed_observer import AppClosedObserver


class DBSession(AppClosedObserver):
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

    def get(self) -> Session:
        return self.session

    def commit(self):
        self.session.commit()

    def on_app_closed(self):
        self.session.commit()
        self.session.close()
