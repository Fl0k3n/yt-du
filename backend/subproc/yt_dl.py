"""
Module is independant of any external modules (excluding standard ones listed below),
when used from another script user should create YTDownloader instance
with appropriate StatusObserver instance for communication.
Then download method should be called.

Downloader downloads passed media links in separate threads, then merges them
using ffmpeg subprocess, stderr of ffmpeg can be obtained.
"""
import sys
import re
import os
from typing import Generator, Iterable, List, Tuple
import requests
from requests import ConnectionError
import threading
from queue import Queue, Empty
from pathlib import Path
import random
from enum import Enum
import time
from abc import ABC, abstractmethod
import urllib.parse as parse


PARENT_DIR = Path(__file__).parent.absolute()


def _get_re_group(reg, data, idx, default):
    try:
        return re.search(reg, data).group(idx)
    except (AttributeError, IndexError):
        return default


def try_del(name, func=os.remove, msg="Failed to cleanup"):
    try:
        func(name)
    except Exception as e:
        print(msg)
        print(type(e), e)


class StatusObserver(ABC):
    """All download methods have to be thread safe"""

    @abstractmethod
    def dl_started(self, idx: int):
        pass

    @abstractmethod
    def dl_finished(self, idx: int):
        pass

    @abstractmethod
    def chunk_fetched(self, idx: int, bytes_len: int):
        pass

    @abstractmethod
    def can_proceed_dl(self, idx: int) -> bool:
        pass

    @abstractmethod
    def merge_started(self):
        pass

    @abstractmethod
    def merge_finished(self, status: int, stderr: str):
        pass

    @abstractmethod
    def dl_error_occured(self, idx: int, exc_type: str, exc_msg: str):
        pass

    @abstractmethod
    def failed_to_init(self, exc_type: str, exc_msg: str):
        pass

    @abstractmethod
    def process_finished(self, success: bool):
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


class MediaURL(ABC):
    """If getting parameter requires extra work lazy init will be used"""
    @abstractmethod
    def get_size(self) -> int:
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
        pass

    @abstractmethod
    def get_raw_url(self) -> str:
        pass

    @classmethod
    @abstractmethod
    def get_required_params(self) -> Iterable[str]:
        pass


class ClenMediaURL(MediaURL):
    """representing urls of form:
    https://r7---sn-x2pm-f5fs.googlevideo.com/videoplayback?expire=1627070421&ei=dcv6YJvXKZX5yQXW2pi4Cg&ip=185.25.121.191&id=o-AHkkLgbS2OUlsLPM2v8g0ZkUUXZFXCDjKKcyI1zCYWE3&itag=399&aitags=133%2C134%2C135%2C136%2C137%2C160%2C242%2C243%2C244%2C247%2C248%2C271%2C278%2C313%2C394%2C395%2C396%2C397%2C398%2C399%2C400%2C401&source=youtube&requiressl=yes&mh=wH&mm=31%2C29&mn=sn-x2pm-f5fs%2Csn-u2oxu-f5fed&ms=au%2Crdu&mv=m&mvi=7&pl=24&initcwndbps=1245000&vprv=1&mime=video%2Fmp4&ns=4afvKawWCex7rzulWwKQk3oG&gir=yes&clen=32646474&dur=187.000&lmt=1627006227864114&mt=1627048609&fvip=1&keepalive=yes&fexp=24001373%2C24007246&c=WEB&txp=5531432&n=PcE-xKRRjcreiA&sparams=expire%2Cei%2Cip%2Cid%2Caitags%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cns%2Cgir%2Cclen%2Cdur%2Clmt&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRAIgdpEbK0XRz4Tt0zd1I4vhVHjOkS7OHaUx4m0-L7zjeScCIG6jwBUH7LVtGMCITc5zIaiMJx4vcAVclta5lQ8OYWa9&alr=yes&sig=AOq0QJ8wRQIhAK_Ktkbx3fx25Hd6qPRNJPucN-3jZXKgWkawTcjzg6lrAiB8uVRvdYmAwuHgbNbDBY5CKfhHVr2YjPmijy_H8xM-xw%3D%3D&cpn=LOfyYmu4lqM5ET_o&cver=2.20210721.00.00&range=0-489233&rn=1&rbuf=0

    i.e. it contains all of params:
    - expire, clen, mime, range
    """

    # bytes, yt throttles chunks > 10MB with this format
    _MAX_CHUNK_SIZE = 10 * 1024 * 1024 - 1
    _REQ_PARAMS = ['clen', 'mime', 'expire', 'range']

    def __init__(self, url: str):
        self.url = url
        query = parse.urlparse(self.url).query
        params = parse.parse_qs(query)
        try:
            self.size = int(params['clen'][0])
            self.mime = params['mime'][0]
            self.exipre = int(params['expire'][0])
        except (KeyError, TypeError) as e:
            raise UnsupportedURLError(self.url, str(e),
                                      msg=f"Failed to build {type(self)} url.")

    def get_raw_url(self) -> str:
        return self.url

    def get_expire_time(self) -> int:
        return self.exipre

    def get_mime(self) -> str:
        return self.mime

    def get_size(self) -> int:
        return self.size

    def generate_chunk_urls(self) -> Generator[Tuple[str, int], None, None]:
        clen = self.get_size()
        range_start = 0
        range_end = self._MAX_CHUNK_SIZE - 1
        link = self.get_raw_url()

        range_re = re.compile(r'(?<=(?:\?|&)range=)(\d+-\d+)')
        if not range_re.search(link):
            raise UnsupportedURLError(link, 'range')

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
    https://r6---sn-x2pm-f5fs.googlevideo.com/videoplayback?expire=1627067155&ei=sr76YNvSOdXWyQWD6ofYCw&ip=185.25.121.191&id=o-ACU8i4GSks1YTq4VLKBpQ8OrUmiNqIrxBjEHzq8511CH&itag=135&aitags=133%2C134%2C135%2C160%2C242%2C243%2C244%2C278&source=yt_otf&requiressl=yes&mh=YV&mm=31%2C29&mn=sn-x2pm-f5fs%2Csn-u2oxu-f5fek&ms=au%2Crdu&mv=m&mvi=6&pl=24&initcwndbps=1415000&vprv=1&mime=video%2Fmp4&ns=pZ6KS-46thYZfqWHmJE9OuYG&otf=1&otfp=1&dur=0.000&lmt=1480857666340217&mt=1627045254&fvip=1&keepalive=yes&fexp=24001373%2C24007246&c=WEB&n=Q1G5m63zPxJShw&sparams=expire%2Cei%2Cip%2Cid%2Caitags%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cns%2Cotf%2Cotfp%2Cdur%2Clmt&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRQIhAKesu1RO61XRpuKCvHVzOSW1d8lbAJIdEuob8H1tNuWYAiAgBZ1D9GudlCzh8LeS3xq5CMhjVIVP3Re_H8MimZfCfQ%3D%3D&alr=yes&sig=AOq0QJ8wRQIhAOMZIBa1p91KoQKh87PCaLh5_7Nkhy_N79APkwtxH64HAiA36LjF3JfL5w63muPKWJ7lNAQca74a9eLj0HB7FhIEgg%3D%3D&cpn=HMIEkbSZlgdAaZFf&cver=2.20210721.00.00&sq=0&rn=1&rbuf=0

    i.e. it contains all of params:
    - expire, mime, sq
    """
    _REQ_PARAMS = ['sq', 'mime', 'expire']
    _MAX_SIZE_FETCHING_THREADS = 10

    def __init__(self, url: str, size: int = None,
                 fetch_retries: int = 5, retry_timeout: int = 0.5):
        self.url = url
        self.size = size
        self.fetch_retries = fetch_retries
        self.retry_timeout = retry_timeout

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

    def _try_request(self, func, *args, **kwargs):
        for _ in range(self.fetch_retries):
            try:
                return func(*args, **kwargs)
            except (ConnectionError, requests.exceptions.Timeout):
                pass

        raise ConnectionError('Failed to get segments count')

    def _get_seg_count(self) -> int:
        if self.seg_count is None:
            resp = self._try_request(requests.get,
                                     self.url, timeout=self.retry_timeout)
            seg_re = r'Segment-Count: (\d+)'
            self.seg_count = int(re.search(seg_re, resp.text).group(1)) + 1

        return self.seg_count

    def _generate_chunk_urls(self) -> Generator[str, None, None]:
        seg_re = r'(?<=\?|&)(sq=(\d+))'
        matches = re.search(seg_re, self.url)

        url_pref = self.url[:matches.start(1)]
        url_suff = self.url[matches.end(1):]

        for i in range(self._get_seg_count()):
            yield f'{url_pref}sq={i}{url_suff}'

    def _fetch_content_len(self):
        while True:
            try:
                idx, url = self.task_queue.get(block=False)
                resp = self._try_request(
                    requests.head, url, timeout=self.retry_timeout)
                self.seg_sizes[idx] = int(resp.headers['Content-Length'])
            except Empty:
                return

    def _get_seg_sizes(self) -> Iterable[int]:
        if self.seg_sizes is None:
            self._init_size_thread_pool()
            for thread in self.threads:
                thread.start()

            for thread in self.threads:
                thread.join()

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

    def generate_chunk_urls(self) -> Generator[Tuple[str, int], None, None]:
        yield from zip(self._generate_chunk_urls(), self._get_seg_sizes())

    @classmethod
    def get_required_params(cls) -> Iterable[str]:
        return cls._REQ_PARAMS


# factory method
def create_media_url(url: str) -> MediaURL:
    classes = [ClenMediaURL, SegmentedMediaURL]
    query = parse.urlparse(url).query
    params = parse.parse_qs(query)

    for cls in classes:
        if all(param in params for param in cls.get_required_params()):
            return cls(url)

    raise UnsupportedURLError(url, msg="Failed to create MediaURL subclass")


class CircularBuffer:
    """For bytes only"""

    def __init__(self, size, fill_val=b''):
        self.size = size
        self.fill_val = fill_val
        self._empty_self()

    def _empty_self(self):
        self.buffer = [self.fill_val] * self.size
        self.start = 0

    def put(self, data):
        # assumes len(data) < size
        l = len(data)
        to_write = min(self.size - self.start, l)
        for i in range(to_write):
            # data[i] converts it to int
            self.buffer[self.start + i] = data[i:i+1]

        left = l - to_write
        for i in range(left):
            self.buffer[i] = data[to_write + i: to_write + i + 1]

        self.start = (self.start + l) % self.size

    def get(self):
        return self.buffer[self.start:] + self.buffer[:self.start]

    def __str__(self):
        return b''.join(self.get()).decode()

    def flush(self):
        data = self.get()
        self._empty_self()
        return data

    def __eq__(self, other):
        if type(other) == bytes:
            return b''.join(self.get()) == other
        return False


class Codes(Enum):
    FETCH_FAILED = 1
    MERGE_FAILED = 2
    SUCCESS = 3


class YTDownloader:
    # bytes, yt throttles chunks > 10MB (probably)
    _MAX_CHUNK_SIZE = 10 * 1024 * 1024 - 1
    try:
        from backend.utils.assets_loader import AssetsLoader as AL
        TMP_DIR = Path(AL.get_env('TMP_FILES_PATH'))
    except ImportError:
        TMP_DIR = PARENT_DIR.joinpath('.tmp')

    def __init__(self, path: str, link: str, data_links: List[str], status_obs: StatusObserver = None,
                 title='unnamed', retry_timeout=5, retries=25, verbose=True, cleanup=True):
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
        self.status_obs = status_obs

        self.playlist_idx = _get_re_group(r'index=(\d+)', link, 1, 0)

        self._create_media_urls()
        self._create_tmp_files_dir()
        self._create_tmp_file_names()

        self._init_thread_pool()

    def _create_media_urls(self):
        try:
            self.media_urls = [create_media_url(
                url) for url in self.data_links]
        except UnsupportedURLError as e:
            print(e)
            if self.status_obs is not None:
                self.status_obs.failed_to_init(type(e), repr(e))

            exit(1)

    def _create_tmp_files_dir(self):
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
        self.file_names = []
        for i, link in enumerate(self.media_urls):
            mime = link.get_mime()
            ext = 'webm' if mime == 'audio/webm' else 'mp4'
            self.file_names.append(Path.joinpath(
                self.tmp_files_dir, f'{i}.{ext}'))

    def _init_thread_pool(self):
        self.thread_status = [0] * len(self.data_links)

        self.threads = [threading.Thread(target=self._fetch, args=(link, media_url, file_name, i))
                        for i, (link, media_url, file_name) in enumerate(
            zip(self.data_links, self.media_urls, self.file_names))]

    def _fetch(self, link, media_url, out_file_path, idx):
        """fetches data links in _MAX_CHUNK sizes then merges them"""
        if self.verbose:
            print(f"[{self.title}] Fetching: {link[:150]}...")

        if self.status_obs is not None:
            self.status_obs.dl_started(idx)

        tmp_file_path = f'{out_file_path}_{idx}'

        with open(out_file_path, 'wb') as f:
            for i, (chunk_link, chunk_size) in enumerate(media_url.generate_chunk_urls()):
                retried = 0
                while True:
                    try:
                        with open(tmp_file_path, 'wb') as tmp_f:
                            r = requests.get(
                                chunk_link, stream=True, timeout=self.retry_timeout, )

                            if not 200 <= r.status_code < 300:
                                raise ValueError(
                                    f'CHUNK: {i} STATUS: {r.status_code}\n HEADERS: {r.headers}')

                            for chunk in r.iter_content(chunk_size=512):
                                tmp_f.write(chunk)

                        if self.status_obs is not None and not self.status_obs.can_proceed_dl(idx):
                            # TODO dl_stopped or smth
                            break

                        # ok chunk read without errors rewrite it to output file
                        with open(tmp_file_path, 'rb') as tmp_f:
                            f.write(tmp_f.read())

                        if self.status_obs is not None:
                            self.status_obs.chunk_fetched(idx, chunk_size)

                        break
                    except Exception as e:
                        print("Failed to fetch.")
                        print(type(e), e)
                        if self.status_obs is not None:
                            self.status_obs.dl_error_occured(idx,
                                                             type(e), repr(e))

                        if retried == self.retries:
                            self.thread_status[idx] = Codes.FETCH_FAILED
                            try_del(tmp_file_path)
                            return
                        retried += 1

        try_del(tmp_file_path)

        self.thread_status[idx] = Codes.SUCCESS

    def _merge_tmp_files(self, accept_all_msgs=True):
        if self.verbose:
            print(f'[{self.title}] Merging.')

        if self.status_obs is not None:
            self.status_obs.merge_started()

        files = []
        for f in self.file_names:
            files.append('-i')
            files.append(f)

        full_err_log = []

        # TODO maybe higher-lvl api
        # just pass stderr of ffmpeg here and if [y/N] is encountered
        # write to its stdin answer

        IN_ME, OUT_FMPEG = os.pipe()
        # IN_FMPEG, OUT_ME = os.pipe()
        if os.fork() == 0:
            os.close(IN_ME)
            # os.close(OUT_ME)

            os.close(sys.stderr.fileno())
            os.close(sys.stdin.fileno())

            os.dup2(OUT_FMPEG, sys.stderr.fileno())
            # os.dup2(IN_FMPEG, sys.stdin.fileno())

            os.execlp("ffmpeg", "ffmpeg", '-y' if accept_all_msgs else '-n',
                      *files, '-c', 'copy', '-strict', 'experimental', self.path)
        else:
            os.close(OUT_FMPEG)
            # os.close(IN_FMPEG)
            # pattern = b'[y/N]'

            # buffer = CircularBuffer(len(pattern))
            while True:
                rd = os.read(IN_ME, 1)  # TODO

                if rd == b'':
                    break
                full_err_log.append(rd)
            #     buffer.put(rd)

            #     if pattern == buffer:
            #         os.write(OUT_ME, b'y\n' if accept_all_msgs else b'N\n')
            #         buffer.flush()

            os.close(IN_ME)
            # os.close(OUT_ME)

            # TODO timeout ?
            _, status = os.wait()
            return Codes.SUCCESS if status == 0 else Codes.MERGE_FAILED, \
                b''.join(full_err_log).decode()

    def _clean_up(self):
        for fname in self.file_names:
            try_del(fname, os.remove)

        for dname in [self.tmp_files_dir]:
            try_del(dname, os.rmdir)

    def download(self):
        """returns True iff downloaded succesfully and ffmpeg stderr log"""

        for thread in self.threads:
            thread.start()

        t_start = time.time()

        status = Codes.SUCCESS  # no errors yet

        # cant zip because not updated data might be generated
        for i, thread in enumerate(self.threads):
            thread.join()
            if self.status_obs is not None:
                self.status_obs.dl_finished(i)

            if self.thread_status[i] != Codes.SUCCESS:
                status = self.thread_status[i]
                print(
                    f"[{self.title}] Aborting, failed to download \n{self.data_links[i]}")
                break

        t_end = time.time()

        if status == Codes.SUCCESS and self.verbose:
            total_c_size = sum(media_url.get_size()
                               for media_url in self.media_urls)

            size = round(total_c_size / 1048576 * 100) / 100  # MB
            t_taken = round((t_end - t_start) * 100) / 100

            print(
                f"[{self.title}] Fetched successfully. SIZE: {size}MB TIME: {t_taken}s")

        if status == Codes.SUCCESS:
            status, err_log = self._merge_tmp_files()
            if self.status_obs is not None:
                self.status_obs.merge_finished(status, err_log)
        else:
            if self.status_obs is not None:
                self.status_obs.process_finished(False)
            # TODO
            return status, 'FAILED AT DL STAGE'

        if status == Codes.SUCCESS and self.verbose:
            print(f"[{self.title}] OK. Merged successfully.")

        if self.cleanup:
            self._clean_up()

        if self.status_obs is not None:
            self.status_obs.process_finished(status == Codes.SUCCESS)

        return status, err_log


def main():
    if len(sys.argv) != 6:
        print(
            f'USAGE: ./{sys.argv[0]} result_path video_url title data_link1 data_link2',
            file=sys.stderr)
        sys.exit(1)

    path, link, title, data_link1, data_link2 = sys.argv[1:]

    ytdl = YTDownloader(path, link, [
        data_link1, data_link2], title=title, verbose=True, cleanup=True)

    status, err_log = ytdl.download()

    if status != Codes.SUCCESS:
        print('-'*20 + 'FAILED TO DOWNLOAD' + '-'*20)
        print(err_log)
    else:
        print(f'OK [{title}] downloaded successfully')

    sys.exit(0)


if __name__ == '__main__':
    main()
