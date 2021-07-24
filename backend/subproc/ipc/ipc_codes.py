from enum import Enum


class ExtCodes(Enum):
    """Codes used for IPC with extension server"""
    # ! keep it consistent with background.js codes

    FETCH_PLAYLIST = 1

    PLAYLIST_FAILED = 3
    PLAYLIST_FETCHED = 4
    PING = 5  # deprecated


class DlCodes(Enum):
    """Codes used for IPC with yt_dl worker"""

    # data: int = index of data link
    DL_STARTED = 1
    # data: int = index of data link
    CAN_PROCEED_DL = 2
    # data: bool = whether dl can be proceeded
    DL_PERMISSION = 3
    # data: tuple(int, int) = (index of data link, bytes dl'ed)
    CHUNK_FETCHED = 4
    # data: int = index of data link
    DL_FINISHED = 5
    #data: None
    MERGE_STARTED = 6
    # data: tuple(int, str) = (ffmpeg exit code, stderr)
    MERGE_FINISHED = 7
    # data: bool = whether process was successful
    PROCESS_FINISHED = 8
