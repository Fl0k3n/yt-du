
from typing import List
from backend.db.db_session import DBSession
from backend.model.data_link import DataLink
from backend.model.db_models import DB_DataLink, DB_Playlist, DB_PlaylistLink
from backend.model.playlist import Playlist
from backend.model.playlist_link import PlaylistLink


class PlaylistRepo:
    def __init__(self, session: DBSession):
        self.session = session

    def create_playlist(self, name: str, url: str, path: str) -> Playlist:
        db_playlist = DB_Playlist(name=name, url=url, path=path)
        self._add(db_playlist)
        return Playlist(db_playlist)

    def create_playlist_link(self, playlist: Playlist, playlist_idx: int, name: str, url: str, path: str) -> PlaylistLink:
        db_playlist_link = DB_PlaylistLink(
            playlist_number=playlist_idx, url=url, title=name, path=path)

        db_playlist_link.playlist = playlist.db_playlist
        db_playlist_link.playlist_id = playlist.db_playlist.playlist_id
        playlist.db_playlist.links.append(db_playlist_link)

        self._add(db_playlist_link)
        pl_link = PlaylistLink(db_playlist_link, playlist)
        playlist.add_playlist_link(pl_link)

        return pl_link

    def create_data_link(self, playlist_link: PlaylistLink, url: str, size: int, mime: str, expire: int) -> DataLink:
        db_data_link = DB_DataLink(
            ulr=url, size=size, mime=mime, expire=expire)

        db_data_link.link = playlist_link.db_link
        db_data_link.playlist_link_id = playlist_link.db_link.link_id
        playlist_link.db_link.data_links.append(db_data_link)

        self._add(db_data_link)
        data_link = DataLink(db_data_link, playlist_link)
        playlist_link.add_data_link(data_link)

        return data_link

    def update(self):
        self.session.commit()

    def _add(self, db_item):
        self.session.get().add(db_item)
        self.session.commit()

    def get_playlist(self, url: str = None, id: int = None) -> Playlist:
        q = self.session.get().query(DB_Playlist)
        if id is not None:
            q = q.filter(DB_Playlist.playlist_id == id)
        if url is not None:
            q = q.filter(DB_Playlist.url == url)

        first = q.first()
        return Playlist(first) if first is not None else None

    def get_playlists(self, offset: int = 0, limit: int = None) -> List[Playlist]:
        db_playlists_query = (self.session.get()
                              .query(DB_Playlist)
                              .order_by(DB_Playlist.added_at.desc())
                              .offset(offset))

        if limit is not None:
            db_playlists_query = db_playlists_query.limit(limit)

        return [Playlist(db_playlist) for db_playlist in db_playlists_query]

    def get_playlist_count(self) -> int:
        return self.session.get().query(DB_Playlist).count()

    def delete_playlist(self, playlist: Playlist):
        self.session.get().delete(playlist.db_playlist)
        self.session.commit()
