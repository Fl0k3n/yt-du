from enum import Enum


class ExtCodes(Enum):
    """Codes used for IPC with extension server"""
    # ! keep it consistent with background.js codes

    TERMINATE = 0

    FETCH_PLAYLIST = 1

    PLAYLIST_FAILED = 3
    PLAYLIST_FETCHED = 4
    PING = 5  # deprecated

    # data: int = number of connections still alive
    LOST_CONNECTION = 6
    CONNECTION_NOT_ESTB = 7

    FETCH_LINK = 8
    LINK_FETCHED = 9


class DlCodes(Enum):
    """Codes used for IPC with yt_dl worker"""
    TERMINATE = 0
    # data: str = absolute path of tmp files dir
    PROCESS_STARTED = 1
    # data: tuple(int, str) = (index of data link, absolute path)
    DL_STARTED = 2
    # data: int = index of data link
    CAN_PROCEED_DL = 3
    # data: tuple(int, bool) = (link_id, whether dl can be proceeded)
    DL_PERMISSION = 4
    # data: tuple(int, int, str) = (index of data link, bytes dl'ed, chunk_url)
    CHUNK_FETCHED = 5
    # data: int = index of data link
    DL_FINISHED = 6
    #data: None
    MERGE_STARTED = 7
    # data: tuple(int, str) = (ffmpeg exit code, stderr)
    MERGE_FINISHED = 8
    # data: bool = whether process was successful
    PROCESS_FINISHED = 9
    # data: None
    PROCESS_STOPPED = 10
    # data: tuple(int, str, str) = (index of data link, type of exception, exception msg)
    DL_ERROR = 11
    # data: tuple(int, MediaURL, str|None) = (link_idx, mediaURL to-be-renewed, url of last successful chunk is this dl session)
    URL_EXPIRED = 12
    # data: tuple(int, MediaURL, bool) = (link_idx, renewed media url, info if its consistent)
    URL_RENEWED = 13
