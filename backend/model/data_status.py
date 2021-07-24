from enum import Enum


class DataStatus(Enum):
    UNDEFINED = 0
    WAIT_FOR_FETCH = 1
    FETCH_URLS = 2
    WAIT_FOR_DL = 3
    DOWNLOADING = 4
    WAIT_FOR_MERGE = 5
    MERGING = 6
    FINISHED = 7

    ERRORS = 8
    PAUSED = 9

    def __str__(self):
        # keep it consistent with these codes
        msgs = [
            'Undefined',
            'Waiting for Fetch',
            'Fetching Urls',
            'Waiting for Download',
            'Downloading',
            'Waiting for Merge',
            'Merging',
            'Finished',
            'Errors',
            'Paused'
        ]

        return msgs[self.value]
