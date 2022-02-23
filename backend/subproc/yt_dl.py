"""
Module is independant of any external modules (excluding the standard ones listed below).
When used from another script the user should create an YTDownloader instance
with appropriate StatusObserver for communication.
Then the YTDownloader.download() method should be called. If the download should be resumed, the user 
has to provide the appropriate Resumer object. If a link has expired and at least 1 renewed 
media link is inconsistent entire data will be cleaned up and the process will abort,
the user should restart the process with renewed data links.

Downloader downloads passed media links in separate threads, then merges them
using ffmpeg subprocess, stderr of ffmpeg can be obtained.

Requirement: ffmpeg version 4.2.4 (not tested with other)
OS: Unix only (tested on Ubuntu 20.04)
Python: 3.8.10
"""
import logging
import sys
import re
import os
import requests
import threading
import random
import time
import urllib.parse as parse
from abc import ABC, abstractmethod
from typing import Generator, Iterable, List, Tuple
from requests import ConnectionError
from queue import Queue, Empty
from pathlib import Path
from enum import Enum


PARENT_DIR = Path(__file__).parent.absolute()


class StatusCode(Enum):
    UNDEFINED = 0
    FETCH_FAILED = 1
    MERGE_FAILED = 2
    SUCCESS = 3
    DL_PERMISSION_DENIED = 4
    INCONSISTENT_RENEW_LINKS = 5


def _get_re_group(reg, data, idx, default):
    try:
        return re.search(reg, data).group(idx)
    except (AttributeError, IndexError):
        return default


def try_del(name, func=os.remove, msg="Failed to cleanup"):
    try:
        func(name)
    except Exception as e:
        logging.exception(msg)


class StatusObserver(ABC):
    """All download, exit, renew methods have to be thread safe"""

    @abstractmethod
    def process_started(self, tmp_files_dir_path: str):
        pass

    @abstractmethod
    def dl_started(self, idx: int, abs_path: str):
        pass

    @abstractmethod
    def dl_finished(self, idx: int):
        pass

    @abstractmethod
    def chunk_fetched(self, idx: int, expected_bytes_len: int,
                      bytes_len: int, chunk_url: str):
        pass

    @abstractmethod
    def can_proceed_dl(self, idx: int) -> bool:
        pass

    # sent if dl permission was denied
    @abstractmethod
    def process_stopped(self):
        pass

    @abstractmethod
    def merge_started(self):
        pass

    @abstractmethod
    def merge_finished(self, status: StatusCode, stderr: str):
        pass

    @abstractmethod
    def dl_error_occured(self, idx: int, exc_type: str, exc_msg: str):
        pass

    @abstractmethod
    def failed_to_init(self, exc_type: str, exc_msg: str):
        pass

    # sent if process terminates itself
    @abstractmethod
    def process_finished(self, success: bool):
        pass

    @abstractmethod
    def thread_started(self):
        """By default thread doesnt allow exit"""
        pass

    @abstractmethod
    def thread_finished(self):
        pass

    # both have to be thread safe
    @abstractmethod
    def forbid_exit(self):
        pass

    @abstractmethod
    def allow_exit(self):
        pass

    # has to be thread safe
    @abstractmethod
    def renew_link(self, idx: int, media_url: "MediaURL", last_successful: str) -> Tuple["MediaURL", bool]:
        """Returns media_url object which next(generate_chunk_urls) will give
        up-to-date url that has failed before calling this method, it also returns bool 
        indicating if dl can be continued using this link."""
        pass

    @abstractmethod
    def allow_subproc_start():
        pass

    @abstractmethod
    def subprocess_started(self, pid: int):
        pass

    @abstractmethod
    def subprocess_finished(self, pid: int):
        pass


class Resumer(ABC):
    @abstractmethod
    def should_create_tmp_files_dir(self) -> bool:
        pass

    @abstractmethod
    def get_tmp_files_dir_path(self) -> Path:
        """If it shouldn't be created, this method should provide absolute path to this dir"""
        pass

    @abstractmethod
    def should_create_tmp_files(self) -> bool:
        pass

    @abstractmethod
    def get_tmp_file_names(self) -> List[Path]:
        """If it shouldn't be created, this method should provide absolute paths to media url files
           order MUST correspond to order of media urls"""
        pass

    @abstractmethod
    def should_resume_download(self) -> bool:
        pass

    @abstractmethod
    def is_resumed(self, url: str) -> bool:
        pass

    @abstractmethod
    def set_resumed(self, url: str):
        pass


class UnsupportedURLError(Exception):
    """Raised when url couldn't have been parsed for downloading"""

    def __init__(self, url, failed_param=None, msg='Unsupported url format.'):
        self.url = url
        self.failed_param = failed_param
        self.msg = msg

    def __str__(self):
        msg = f'{self.msg}\nFailed for [{self.url}]'
        if self.failed_param:
            msg += f' param [{self.failed_param}] not found.'
        return msg


class MediaURLType(Enum):
    CLEN = 1
    SEQ = 2


class MediaURL(ABC):
    """If getting parameter requires extra work lazy init will be used"""

    def __init__(self, url: str, resumed: bool = False,
                 fetch_retries: int = 25, retry_timeout: float = 1):
        self.url = url
        self.resumed = resumed
        self.fetch_retries = fetch_retries
        self.retry_timeout = retry_timeout

    @abstractmethod
    def get_media_type(self) -> MediaURLType:
        pass

    @abstractmethod
    def get_size(self) -> int:
        pass

    @abstractmethod
    def set_size(self, size: int):
        pass

    @abstractmethod
    def get_expire_time(self) -> int:
        # epoch time (probably)
        pass

    @abstractmethod
    def get_mime(self) -> str:
        pass

    @abstractmethod
    def generate_chunk_urls(self) -> Generator[Tuple[str, int], None, None]:
        """Yields pairs of chunk_url, expected chunk_size (bytes)"""
        pass

    @abstractmethod
    def get_raw_url(self) -> str:
        pass

    def is_expired(self) -> bool:
        return time.time() >= self.get_expire_time()

    @staticmethod
    def _get_query_params(url: str):
        return parse.parse_qs(parse.urlparse(url).query)

    @abstractmethod
    def _get_renew_params(self) -> List[str]:
        pass

    def renew(self, renewed_url: "MediaURL", last_successful: str):
        url = renewed_url.get_raw_url()

        if last_successful is None:
            if not self.resumed:
                self.url = url
                return
            last_successful = self.url

        self.expire = renewed_url.get_expire_time()

        # TODO large segmented urls might fail here, need other methods
        # size = renewed_url.get_size()

        # if size != self.get_size():
        #     raise UnsupportedURLError(url, msg='Sizes do not match')

        # TODO use ffprobe to get resolution and other such data
        # would require saving it for previous url in the first place

        old_state_params = self._get_query_params(last_successful)
        try:
            names = self._get_renew_params()
            values = [old_state_params[name][0] for name in names]
        except (KeyError) as e:
            raise UnsupportedURLError(last_successful, str(
                e), msg=f'Failed to extract state params')

        self.url = url

        for name, val in zip(names, values):
            rg = r'(?<=(?:\?|&)' + name + r'=)(.*?)(?=&|$)'
            self.url = re.sub(rg, val, self.url)

        self.resumed = True

    @classmethod
    @abstractmethod
    def get_required_params(self) -> Iterable[str]:
        pass


def try_request(retries, func, *args, **kwargs):
    for _ in range(retries):
        try:
            return func(*args, **kwargs)
        except (ConnectionError, requests.exceptions.Timeout):
            pass

    raise ConnectionError('Failed to execute ', repr(func), 'with args', args)


class ClenMediaURL(MediaURL):
    """representing urls of form:
    https://r7---sn-x2pm-f5fs.googlevideo.com/videoplayback?expire=1627070421&ei=...&ip=...&id=...&itag=...&aitags=...&source=youtube&requiressl=yes&mh=...&mn=...&mvi=7&pl=...&initcwndbps=...&vprv=1&mime=video%2Fmp4&ns=4afvKawWCex7rzulWwKQk3oG&gir=yes&clen=32646474&dur=187.000&lmt=...&mt=...&fvip=1&keepalive=yes&fexp=...&c=WEB&txp=...&n=...&sparams=expire%2Cei%2Cip%2Cid%2Caitags%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cns%2Cgir%2Cclen%2Cdur%2Clmt&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=...9&alr=...&sig=...&cpn=...&cver=2.20210721.00.00&range=0-489233&rn=1&rbuf=0

    i.e. it contains all of params:
    - expire, clen, mime, range
    """

    # bytes, yt throttles chunks > 10MB (MB instead of MiB for safety) with this format
    # for now 2MB is used for better responsiveness
    _MAX_CHUNK_SIZE = 2 * 1000 * 1000 - 1
    _REQ_PARAMS = ['clen', 'mime', 'expire', 'range']
    _MAX_REDIRECTS = 10

    def __init__(self, url: str, resumed: bool = False,
                 fetch_retries: int = 25, retry_timeout: float = 1):
        super().__init__(url=url, resumed=resumed,
                         fetch_retries=fetch_retries, retry_timeout=retry_timeout)

        params = self._get_query_params(self.url)
        try:
            self.size = int(params['clen'][0])
            self.mime = params['mime'][0]
            self.exipre = int(params['expire'][0])
        except (KeyError, TypeError) as e:
            raise UnsupportedURLError(self.url, str(e),
                                      msg=f"Failed to build {type(self)} url.")

        if not self.resumed:  # TODO Do it either way?
            self._fix_redirects()

    def _fix_redirects(self):
        for _ in range(self._MAX_REDIRECTS):
            resp = try_request(self.fetch_retries, requests.get,
                               self.url, self.retry_timeout)
            hdrs = resp.headers
            if hdrs['Content-Type'] == 'text/plain' and resp.text.startswith('https'):
                self.url = resp.text
            else:
                break
            # handle other error codes?

    def get_raw_url(self) -> str:
        return self.url

    def get_expire_time(self) -> int:
        return self.exipre

    def get_mime(self) -> str:
        return self.mime

    def get_size(self) -> int:
        return self.size

    def set_size(self, size: int):
        self.size = size

    def get_media_type(self) -> MediaURLType:
        return MediaURLType.CLEN

    def _get_renew_params(self) -> List[str]:
        return ['range', 'rn', 'rbuf']

    def generate_chunk_urls(self) -> Generator[Tuple[str, int], None, None]:
        clen = self.get_size()
        link = self.get_raw_url()

        range_re = re.compile(r'(?<=(?:\?|&)range=)(\d+-\d+)')

        try:
            base_r_start, base_r_end = [
                int(x) for x in range_re.search(link).group(1).split('-')]
        except Exception as e:
            raise UnsupportedURLError(link, 'range', str(e))

        # already finished
        if self.resumed and base_r_end == clen - 1:
            return

        get_next = False

        if base_r_start == 0:
            if base_r_end == self._MAX_CHUNK_SIZE - 1 and self.resumed:
                get_next = True
            else:
                range_start = 0
                range_end = self._MAX_CHUNK_SIZE - 1
        else:
            get_next = True
            if not self.resumed:
                raise AttributeError(
                    'first chunk url starting at unexpected position ', self.get_raw_url())

        if get_next:
            range_start = base_r_end + 1
            range_end = base_r_end + self._MAX_CHUNK_SIZE

        end_found = False

        while not end_found:
            if range_end >= clen:
                range_end = clen - 1
                end_found = True

            # TODO would be more efficient to just find index of it, left for readability
            chunk_link = range_re.sub(f'{range_start}-{range_end}', link)
            yield chunk_link, range_end - range_start + 1
            range_start = range_end + 1
            range_end += self._MAX_CHUNK_SIZE

    @classmethod
    def get_required_params(cls) -> Iterable[str]:
        return cls._REQ_PARAMS


class SegmentedMediaURL(MediaURL):
    """representing urls of form:
    https://r6---sn-x2pm-f5fs.googlevideo.com/videoplayback?expire=1627067155&ei=...&ip=...&id=...&itag=135&aitags=1...&source=yt_otf&requiressl=yes&mh=...&mm=...&mn=...&mv=m&mvi=6&pl=...&initcwndbps=...&vprv=1&mime=video%2Fmp4&ns=...&otf=1&otfp=1&dur=0.000&lmt=...&mt=...&fvip=1&keepalive=yes&fexp=...&c=WEB&n=...&sparams=expire%2Cei%2Cip%2Cid%2Caitags%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cns%2Cotf%2Cotfp%2Cdur%2Clmt&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=...&alr=yes&sig=...&cpn=...&cver=2.20210721.00.00&sq=0&rn=1&rbuf=0

    i.e. it contains all of params:
    - expire, mime, sq
    """
    _REQ_PARAMS = ['sq', 'mime', 'expire']
    _MAX_SIZE_FETCHING_THREADS = 10
    # If video has more than that segments
    # fetching will take too much time TODO get rid of it totally?
    _MAX_SEGMENTS_TO_FETCH_SIZE = 50
    _MAX_REDIRECTS = 10

    def __init__(self, url: str, size: int = None,
                 fetch_retries: int = 25, retry_timeout: float = 1, resumed: bool = False):
        super().__init__(url=url, resumed=resumed,
                         fetch_retries=fetch_retries, retry_timeout=retry_timeout)
        self.size = size

        self.redirected_count = 0
        self.seg_count = None
        self.seg_sizes = None
        query = parse.urlparse(self.url).query
        params = parse.parse_qs(query)
        try:
            self.mime = params['mime'][0]
            self.exipre = int(params['expire'][0])
        except (KeyError, TypeError) as e:
            raise UnsupportedURLError(self.url, str(e),
                                      msg=f"Failed to build {type(self)} url.")

    def _get_expected_chunk_size(self) -> int:
        # TODO, based on quality or mean of first couple
        return 150000

    def _init_size_thread_pool(self):
        self.task_queue = Queue()
        self.threads = []

        for i, url in enumerate(self._generate_chunk_urls()):
            self.task_queue.put((i, url))

        for i in range(
                min(self._MAX_SIZE_FETCHING_THREADS, self._get_seg_count())):
            self.threads.append(threading.Thread(
                target=self._fetch_content_len))

        self.seg_sizes = [None] * self._get_seg_count()

    def _get_seg_count(self) -> int:
        if self.seg_count is None:
            if self.resumed:
                first_link = re.sub(r'(?<=\?|&)(sq=(\d+))',
                                    'sq=0', self.get_raw_url())
            else:
                first_link = self.get_raw_url()

            resp = try_request(self.fetch_retries, requests.get,
                               first_link, timeout=self.retry_timeout)
            seg_re = r'Segment-Count: (\d+)'
            try:
                self.seg_count = int(re.search(seg_re, resp.text).group(1)) + 1
            except AttributeError:  # redirected most likely
                if self.redirected_count == self._MAX_REDIRECTS:
                    raise  # stop infinite recursion

                hdrs = resp.headers
                if hdrs['Content-Type'] == 'text/plain' and resp.text.startswith('https'):
                    self.url = resp.text
                    self.redirected_count += 1
                    return self._get_seg_count()

                raise

        return self.seg_count

    def _generate_chunk_urls(self) -> Generator[str, None, None]:
        seg_re = r'(?<=\?|&)(sq=(\d+))'

        try:
            matches = re.search(seg_re, self.get_raw_url())

            url_pref = self.url[:matches.start(1)]
            url_suff = self.url[matches.end(1):]

            last_seg = int(matches.group(2))
        except Exception as e:
            raise UnsupportedURLError(self.get_raw_url(), 'sq', str(e))

        if last_seg > 0 and not self.resumed:
            raise AttributeError(
                'first chunk url starting at unexpected position ', self.get_raw_url())

        if last_seg == 0 and not self.resumed:
            last_seg = -1

        # already finished
        if self.resumed and last_seg == self._get_seg_count() - 1:
            return

        for i in range(last_seg + 1, self._get_seg_count()):
            yield f'{url_pref}sq={i}{url_suff}'

    def _fetch_content_len(self):
        while True:
            try:
                idx, url = self.task_queue.get(block=False)
                resp = try_request(self.fetch_retries,
                                   requests.head, url, timeout=self.retry_timeout)
                self.seg_sizes[idx] = int(resp.headers['Content-Length'])
            except Empty:
                return

    def _get_seg_sizes(self) -> Iterable[int]:
        if self.seg_sizes is None:
            if self._get_seg_count() < self._MAX_SEGMENTS_TO_FETCH_SIZE:
                self._init_size_thread_pool()
                for thread in self.threads:
                    thread.start()

                for thread in self.threads:
                    thread.join()
            else:
                self.seg_sizes = [
                    self._get_expected_chunk_size()] * self._get_seg_count()
        return self.seg_sizes

    def _get_size(self) -> int:
        return sum(self._get_seg_sizes())

    def get_raw_url(self) -> str:
        return self.url

    def get_expire_time(self) -> int:
        return self.exipre

    def get_mime(self) -> str:
        return self.mime

    def get_size(self) -> int:
        if self.size is None:
            self.size = self._get_size()

        return self.size

    def get_media_type(self) -> MediaURLType:
        return MediaURLType.SEQ

    def set_size(self, size: int):
        self.size = size

    def _get_renew_params(self) -> List[str]:
        return ['sq', 'rn', 'rbuf']

    def generate_chunk_urls(self) -> Generator[Tuple[str, int], None, None]:
        yield from zip(self._generate_chunk_urls(), self._get_seg_sizes())

    @classmethod
    def get_required_params(cls) -> Iterable[str]:
        return cls._REQ_PARAMS


# factory method
def create_media_url(url: str, resumed: bool = False) -> MediaURL:
    classes = [ClenMediaURL, SegmentedMediaURL]
    query = parse.urlparse(url).query
    params = parse.parse_qs(query)

    for cls in classes:
        if all(param in params for param in cls.get_required_params()):
            return cls(url, resumed=resumed)

    raise UnsupportedURLError(url, msg="Failed to create MediaURL subclass")


class YTDownloader:
    try:
        from backend.utils.assets_loader import AssetsLoader as AL
        TMP_DIR = Path(AL.get_env('TMP_FILES_PATH'))
    except ImportError:
        TMP_DIR = PARENT_DIR.joinpath('.tmp')

    def __init__(self, path: str, link: str, data_links: List[str], status_obs: StatusObserver = None,
                 title='unnamed', retry_timeout=5, retries=25, resumed=False, resumer: Resumer = None, verbose=True, cleanup=True):
        """
        Args:
            path (string): absolute path to file where downloaded video should be saved
            link (string): url to video to download
            data_links ([string]): array of data links, for now each video should have 2 (audio.webm + video.mp4)
            title (string): title of video, needed only for logging
            retry_timeout(float): seconds after each request is timed out, can be lower if not much parallel dls are performed
            retries (int): how many times each request should be retried
            verbose (bool): print status to stdout
            cleanup (bool): delete individual media files after merge succeeds
        """
        self.path = path
        self.link = link
        self.title = title
        self.data_links = data_links
        self.retry_timeout = retry_timeout
        self.retries = retries
        self.verbose = verbose
        self.cleanup = cleanup
        self.resumed = resumed
        self.resumer = resumer
        self.status_obs = status_obs

        if self.resumed and resumer is None:
            raise AttributeError('Resumer is required for resume mode')

        if self.status_obs is not None:
            self.status_obs.allow_exit()

        self.playlist_idx = _get_re_group(r'index=(\d+)', link, 1, 0)

        self._create_media_urls()
        self._create_tmp_files_dir()
        self._create_tmp_file_names()

        self._init_thread_pool()

        if self.status_obs is not None:
            self.status_obs.process_started(str(self.tmp_files_dir.absolute()))

    def _create_media_urls(self):
        try:
            self.media_urls = [create_media_url(
                url, self.resumed and self.resumer.is_resumed(url))
                for url in self.data_links]
        except UnsupportedURLError as e:
            print(e)
            if self.status_obs is not None:
                self.status_obs.failed_to_init(type(e), repr(e))

            exit(1)

    def _create_tmp_files_dir(self):
        if self.resumed and not self.resumer.should_create_tmp_files_dir():
            self.tmp_files_dir = self.resumer.get_tmp_files_dir_path()
            return

        try:
            os.mkdir(self.TMP_DIR)
        except FileExistsError:
            pass

        try:
            # increase chance of uniqueness
            self.tmp_files_dir = Path.joinpath(self.TMP_DIR, f'{self.playlist_idx}_' + str(
                abs(hash(self.link))) + f'_{random.randint(1, 99)}')
            os.mkdir(self.tmp_files_dir)
        except FileExistsError:
            pass

    def _create_tmp_file_names(self):
        if self.resumed and not self.resumer.should_create_tmp_files():
            self.file_names = self.resumer.get_tmp_file_names()
            return

        self.file_names = []
        for i, link in enumerate(self.media_urls):
            mime = link.get_mime()
            ext = 'webm' if mime == 'audio/webm' else 'mp4'
            self.file_names.append(Path.joinpath(
                self.tmp_files_dir, f'{i}.{ext}'))

    def _init_thread_pool(self):
        if self.resumed and not self.resumer.should_resume_download():
            return

        self.thread_status = [StatusCode.UNDEFINED] * len(self.data_links)

        self.threads = [threading.Thread(target=self._fetch, args=(link, media_url, file_name, i))
                        for i, (link, media_url, file_name) in enumerate(
            zip(self.data_links, self.media_urls, self.file_names))]

    def _fetch(self, link: str, media_url: MediaURL, out_file_path: Path, idx: int):
        """fetches data links in chunks"""
        if self.status_obs is not None:
            self.status_obs.dl_started(idx, str(out_file_path))

        if self.verbose:
            logging.debug(f"[{self.title}] Fetching: {link[:150]}...")

        tmp_file_path = f'{out_file_path}_{idx}'

        if self.resumed and self.resumer.should_resume_download():
            f_mode = 'ab'
        else:
            f_mode = 'wb'

        chunk_gen = enumerate(media_url.generate_chunk_urls())
        last_successful = None

        with open(out_file_path, f_mode) as f:
            # raw 'for loop' so generator can be changed during iteration
            while True:
                try:
                    i, (chunk_link, expected_chunk_size) = next(chunk_gen)
                except StopIteration:
                    break

                retried = 0
                while True:
                    try:
                        r = requests.get(
                            chunk_link, stream=True, timeout=self.retry_timeout)

                        if r.headers['Content-Length'] == '0' and media_url.is_expired():
                            if self.status_obs is None:
                                logging.warning(
                                    f'{link} has expired, aborting.')
                                self.thread_status[idx] = StatusCode.FETCH_FAILED
                                try_del(tmp_file_path)
                                return
                            media_url, is_consistent = self.status_obs.renew_link(idx,
                                                                                  media_url, last_successful)

                            if not is_consistent:
                                logging.warning(
                                    'links are inconsistent, aborting')
                                self.thread_status[idx] = StatusCode.INCONSISTENT_RENEW_LINKS
                                try_del(tmp_file_path)
                                return

                            chunk_gen = enumerate(
                                media_url.generate_chunk_urls(), i)
                            break

                        if not 200 <= r.status_code < 300:
                            raise ValueError(
                                f'CHUNK: {i} STATUS: {r.status_code}\n HEADERS: {r.headers}')

                        with open(tmp_file_path, 'wb') as tmp_f:
                            for chunk in r.iter_content(chunk_size=512):
                                tmp_f.write(chunk)

                        if self.status_obs is not None and not self.status_obs.can_proceed_dl(idx):
                            self.thread_status[idx] = StatusCode.DL_PERMISSION_DENIED
                            try_del(tmp_file_path)
                            return

                        # if process gets terminated while writing this chunk
                        # entire file may become useless
                        if self.status_obs is not None:
                            self.status_obs.forbid_exit()

                        # ok chunk read without errors rewrite it to output file
                        with open(tmp_file_path, 'rb') as tmp_f:
                            f.write(tmp_f.read())

                        f.flush()

                        chunk_size = int(r.headers['Content-Length'])

                        if self.status_obs is not None:
                            self.status_obs.chunk_fetched(
                                idx, expected_chunk_size, chunk_size, chunk_link)
                            self.status_obs.allow_exit()

                        last_successful = chunk_link

                        break
                    except Exception as e:
                        logging.exception("Failed to fetch.")
                        if self.status_obs is not None:
                            self.status_obs.dl_error_occured(idx,
                                                             type(e), repr(e))

                        if retried == self.retries:
                            self.thread_status[idx] = StatusCode.FETCH_FAILED
                            try_del(tmp_file_path)
                            return
                        retried += 1

        try_del(tmp_file_path)

        self.thread_status[idx] = StatusCode.SUCCESS

    def _merge_tmp_files(self, accept_all_msgs=True):
        if self.verbose:
            logging.debug(f'[{self.title}] Merging.')

        if self.status_obs is not None:
            self.status_obs.merge_started()

        files = []
        for f in self.file_names:
            files.append('-i')
            files.append(f)

        full_err_log = []

        # TODO maybe higher-lvl api

        IN_ME, OUT_FMPEG = os.pipe()

        if self.status_obs is not None:
            self.status_obs.allow_subproc_start()

        pid = os.fork()
        if pid == 0:
            os.close(IN_ME)

            os.close(sys.stderr.fileno())
            os.close(sys.stdin.fileno())

            os.dup2(OUT_FMPEG, sys.stderr.fileno())

            os.execlp("ffmpeg", "ffmpeg", '-y' if accept_all_msgs else '-n',
                      *files, '-c', 'copy', '-strict', 'experimental', self.path)
        else:
            if self.status_obs is not None:
                self.status_obs.subprocess_started(pid)

            os.close(OUT_FMPEG)
            while True:
                rd = os.read(IN_ME, 1)  # TODO

                if rd == b'':
                    break
                full_err_log.append(rd)

            os.close(IN_ME)

            pid_, status = os.wait()

            if self.status_obs is not None:
                self.status_obs.subprocess_finished(pid)

            return StatusCode.SUCCESS if status == 0 else StatusCode.MERGE_FAILED, \
                b''.join(full_err_log).decode()

    def _clean_up(self):
        for fname in self.file_names:
            try_del(fname, os.remove)

        for dname in [self.tmp_files_dir]:
            try_del(dname, os.rmdir)

    def download(self):
        """returns True iff downloaded succesfully and ffmpeg stderr log"""
        if not self.resumed or \
                (self.resumed and self.resumer.should_resume_download()):
            status = self._fetch_all()

            if status == StatusCode.DL_PERMISSION_DENIED:
                return 0, 'DL PERMISSION DENIED'
            if status == StatusCode.INCONSISTENT_RENEW_LINKS and self.cleanup:
                # if they are inconsistent all of that data is most likely useless
                # process should be run again with renewed links
                self._clean_up()
        else:
            status = StatusCode.SUCCESS

        if status == StatusCode.SUCCESS:
            status, err_log = self._merge_tmp_files()
            if self.status_obs is not None:
                self.status_obs.merge_finished(status, err_log)
        else:
            if self.status_obs is not None:
                self.status_obs.process_finished(False)
            # TODO
            return status, 'FAILED AT DL STAGE'

        if status == StatusCode.SUCCESS and self.verbose:
            logging.debug(f"[{self.title}] OK. Merged successfully.")

        if status == StatusCode.SUCCESS and self.cleanup:
            self._clean_up()

        if self.status_obs is not None:
            self.status_obs.process_finished(status == StatusCode.SUCCESS)

        return status, err_log

    def _fetch_all(self) -> StatusCode:
        for thread in self.threads:
            # possible race condition if called after
            if self.status_obs is not None:
                self.status_obs.thread_started()
                self.status_obs.allow_exit()
            thread.start()

        t_start = time.time()

        status = StatusCode.SUCCESS  # no errors yet

        permission_denied = False
        inconsitent_renew = False

        # cant zip because not updated data might be generated
        for i, thread in enumerate(self.threads):
            thread.join()

            if self.status_obs is not None:
                self.status_obs.thread_finished()

            if self.thread_status[i] == StatusCode.DL_PERMISSION_DENIED:
                permission_denied = True
                # all threads have to be joined
                continue
            elif self.thread_status[i] == StatusCode.INCONSISTENT_RENEW_LINKS:
                inconsitent_renew = True
                continue

            if self.status_obs is not None:
                self.status_obs.dl_finished(i)

            if self.thread_status[i] not in {StatusCode.SUCCESS, StatusCode.DL_PERMISSION_DENIED}:
                status = self.thread_status[i]
                logging.info(
                    f"[{self.title}] Aborting, failed to download \n{self.data_links[i]}")
                break

        if inconsitent_renew:
            return StatusCode.INCONSISTENT_RENEW_LINKS

        if permission_denied:
            logging.info('dl permission denied, exiting')
            if self.status_obs is not None:
                self.status_obs.process_stopped()
            return StatusCode.DL_PERMISSION_DENIED

        t_end = time.time()

        if status == StatusCode.SUCCESS and self.verbose:
            total_c_size = sum(media_url.get_size()
                               for media_url in self.media_urls)

            size = round(total_c_size / 1048576 * 100) / 100  # MB
            t_taken = round((t_end - t_start) * 100) / 100

            logging.info(
                f"[{self.title}] Fetched successfully. SIZE: {size}MB TIME: {t_taken}s")

        return status


def main():
    if len(sys.argv) != 6:
        print(
            f'USAGE: ./{sys.argv[0]} result_path video_url title data_link1 data_link2',
            file=sys.stderr)
        sys.exit(1)

    logger_format = '[%(filename)s:%(lineno)d] %(levelname)-8s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=logger_format)

    path, link, title, data_link1, data_link2 = sys.argv[1:]

    ytdl = YTDownloader(path, link, [
        data_link1, data_link2], title=title, verbose=True, cleanup=True)

    status, err_log = ytdl.download()

    if status != StatusCode.SUCCESS:
        logging.error('-'*20 + 'FAILED TO DOWNLOAD' + '-'*20 + f'\n{err_log}')
    else:
        logging.info(f'OK [{title}] downloaded successfully')

    sys.exit(0)


if __name__ == '__main__':
    main()
