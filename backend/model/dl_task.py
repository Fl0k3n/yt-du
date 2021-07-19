
from typing import List


class DlTask:
    def __init__(self, dest_path: str, url: str, media_urls: List[str]):
        self.dest_path = dest_path
        self.url = url
        self.media_urls = media_urls
