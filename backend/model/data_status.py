from enum import Enum


class DataStatus(Enum):
    UNDEFINED = 0
    WAIT_FOR_FETCH = 1
    FETCH_URLS = 2
    WAIT_FOR_DL = 3
    DOWNLOADING = 4
    MERGING = 5
    FINISHED = 6

    ERRORS = 7
    PAUSED = 8

    def __str__(self):
        # keep it consistent with these codes
        msgs = [
            'Undefined'
            'Waiting for Fetch',
            'Fetching Urls',
            'Waiting for Download',
            'Downloading',
            'Merging',
            'Finished',
            'Errors',
            'Paused'
        ]

        return msgs[self.value]
