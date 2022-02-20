from sqlalchemy import Column, Integer, String, ForeignKey, Table, Text, TIMESTAMP, Boolean
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func, text
from backend.model.downloadable import Downloadable

Base = declarative_base()

# many-to-many table, each merge uses >= 1 data_link and data_link can be used in more
# than one merge (e.g. if used cmd fail) (TODO)
merge_data_links = Table(
    "merge_data_links",
    Base.metadata,
    Column("merge_id", Integer, ForeignKey("merge_data.merge_id")),
    Column("data_link_id", Integer, ForeignKey("data_links.link_id"))
)


class DB_Playlist(Base, Downloadable):
    """Contains top-level info about playlist, name should be filename at which it should be saved,
    url should be of the form: https://www.youtube.com/watch?v=...&list=...
    """
    __tablename__ = 'playlists'
    playlist_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    directory_path = Column(Text, nullable=False)
    added_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    finished_at = Column(TIMESTAMP, nullable=True)
    status = Column(Integer, nullable=False, server_default=text('0'))
    links = relationship("DB_PlaylistLink", back_populates="playlist",
                         order_by="DB_PlaylistLink.playlist_number",
                         cascade="all, delete")


class DB_PlaylistLink(Base, Downloadable):
    """Info about specific playlist item, title will be used as filename"""
    __tablename__ = 'playlist_links'
    link_id = Column(Integer, primary_key=True, autoincrement=True)
    playlist_number = Column(Integer, nullable=False)
    url = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    playlist_id = Column(Integer, ForeignKey(
        'playlists.playlist_id'), nullable=False)
    cleaned_up = Column(Boolean, nullable=False, default=False)
    status = Column(Integer, nullable=False, server_default=text('0'))
    path = Column(Text, nullable=False)
    tmp_files_dir = Column(Text, nullable=True)

    playlist = relationship("DB_Playlist", back_populates="links")
    data_links = relationship(
        'DB_DataLink', back_populates='link', cascade="all, delete")
    merges = relationship('DB_MergeData', back_populates='link')


class DB_DataLink(Base):
    """Link to specific media, downloaded contains size in bytes of data saved at path"""
    __tablename__ = 'data_links'
    link_id = Column(Integer, primary_key=True, autoincrement=True)
    playlist_link_id = Column(Integer, ForeignKey(
        'playlist_links.link_id'), nullable=False)
    url = Column(Text, nullable=False)
    mime = Column(String(50), nullable=False)
    expire = Column(Integer, nullable=False)  # epoch time
    size = Column(Integer, nullable=False)
    path = Column(Text, nullable=True)
    downloaded = Column(Integer, nullable=False, default=0)
    download_start_time = Column(TIMESTAMP, nullable=True)
    last_chunk_url = Column(Text, nullable=True)

    link = relationship('DB_PlaylistLink', back_populates='data_links')
    error_logs = relationship('DB_DownloadErrorLog',
                              back_populates='data_link')


class DB_DownloadErrorLog(Base):
    """Msg should contain any text indicating what has failed,
     i.e. Exception type or HTTP status, headers..."""
    __tablename__ = 'download_error_log'
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    data_link_id = Column(Integer, ForeignKey(
        'data_links.link_id'), nullable=False)
    log_time = Column(TIMESTAMP, nullable=False, server_default=func.now())
    msg = Column(Text, nullable=False)

    data_link = relationship('DB_DataLink', back_populates='error_logs')


class DB_MergeStatus(Base):
    """Dictionary containig valid merge_status (success, aborted, fail1(reason), fail2)..."""
    __tablename__ = 'merge_status'
    status_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)


class DB_MergeData(Base):
    """Contains info about merge try, cmd should contain exec arg list"""
    __tablename__ = 'merge_data'
    merge_id = Column(Integer, primary_key=True, autoincrement=True)
    playlist_link_id = Column(Integer, ForeignKey(
        'playlist_links.link_id'), nullable=False)
    status_id = Column(Integer, ForeignKey(
        'merge_status.status_id'), nullable=False)
    cmd = Column(Text, nullable=False)
    proc_exit_code = Column(Integer)
    start_time = Column(TIMESTAMP)

    link = relationship('DB_PlaylistLink', back_populates='merges')
    data_links = relationship('DB_DataLink', secondary=merge_data_links)
    error_logs = relationship('DB_MergeErrorLog', back_populates='merge')


class DB_MergeErrorLog(Base):
    """msg should contain stderr of ffmpeg and/or other exception(s) info"""
    __tablename__ = 'merge_error_log'
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    merge_id = Column(Integer, ForeignKey(
        'merge_data.merge_id'), nullable=False)
    log_time = Column(TIMESTAMP, nullable=False, server_default=func.now())
    msg = Column(Text, nullable=False)

    merge = relationship('DB_MergeData', back_populates='error_logs')
