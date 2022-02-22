import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from backend.model.db_models import Base
from backend.utils.assets_loader import AssetsLoader as AL
from backend.controller.app_closed_observer import AppClosedObserver


class DBSession(AppClosedObserver):
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.engine = None
        self.session = None

    def connect(self):
        logging.info('connecting to db...')
        username, password, address, name = [
            AL.get_env('DB_' + x) for x in ['USERNAME', 'PASSWORD', 'ADDRESS', 'NAME']]

        self.engine = create_engine(
            f'postgresql+psycopg2://{username}:{password}@{address}/{name}',
            echo=self.verbose, future=True)

        Base.metadata.create_all(self.engine)

        self.session = Session(self.engine)

        logging.info('db connected')

    def get(self) -> Session:
        return self.session

    def commit(self):
        self.session.commit()

    def on_app_closed(self):
        self.session.commit()
        self.session.close()
