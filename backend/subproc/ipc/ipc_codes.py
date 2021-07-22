from enum import Enum


class ExtCodes(Enum):
    # ! keep it consistent with background.js codes

    FETCH_PLAYLIST = 1

    PLAYLIST_FAILED = 3
    PLAYLIST_FETCHED = 4
    PING = 5  # deprecated


class DlCodes(Enum):
    DL_STARTED = 1  # data: int = index of data link
