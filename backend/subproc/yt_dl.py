import sys
import re
import os
from typing import List
import requests
import threading
from pathlib import Path
import urllib
import random
from enum import Enum
import time
from backend.utils.assets_loader import AssetsLoader as AL
from abc import ABC, abstractmethod

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
    def dl_error_occured(self, idx:int, exc_type: str, exc_msg: str):
        pass

    @abstractmethod
    def process_finished(self):
        pass


class UnsupportedURLError(Exception):
    """Raised when url couldn't have been parsed for downloading"""

    def __init__(self, url, failed_param, msg='Unsupported url format.'):
        self.url = url
        self.failed_param = failed_param
        self.msg = msg

    def __str__(self):
        return f'{self.msg}\nFailed for [{self.url}], param [{self.failed_param}] not found.'


class CircularBuffer:
    def __init__(self, size):
        self.size = size
        self._empty_self()

    def _empty_self(self):
        self.buffer = ['' for _ in range(self.size)]
        self.start = 0

    def put(self, data):
        # assumes len(data) < size
        l = len(data)
        to_write = min(self.size - self.start, l)
        for i in range(to_write):
            self.buffer[self.start + i] = data[i]

        left = l - to_write
        for i in range(left):
            self.buffer[i] = data[to_write + i]

        self.start = (self.start + l) % self.size

    def get(self):
        return self.buffer[self.start:] + self.buffer[:self.start]

    def __str__(self):
        # only for str-like types
        return ''.join(self.get())

    def flush(self):
        data = self.get()
        self._empty_self()
        return data


class Codes(Enum):
    FETCH_FAILED = 1
    MERGE_FAILED = 2
    SUCCESS = 3


class YTDownloader:
    # bytes, yt throttles chunks > 10MB (probably)
    _MAX_CHUNK_SIZE = 10 * 1024 * 1024 - 1
    TMP_DIR = Path(AL.get_env('TMP_FILES_PATH'))

    def __init__(self, path: str, link: str, data_links: List[str], status_obs: StatusObserver = None,
                 title='unnamed', retries=3, verbose=True, cleanup=True):
        """
        Args:
            path (string): absolute path to file where downloaded video should be saved
            link (string): url to video to download
            data_links ([string]): array of data links, for now each video should have 2 (audio.webm + video.mp4)
            title (string): title of video, needed only for logging
            retries (int): how many times download should be retried
            verbose (bool): print status to stdout
            cleanup (bool): delete individual media files after merge succeeds
        """
        self.path = path
        self.link = link
        self.title = title
        self.data_links = data_links
        self.retries = retries
        self.verbose = verbose
        self.cleanup = cleanup
        self.status_obs = status_obs

        self.playlist_idx = _get_re_group(r'index=(\d+)', link, 1, 0)

        self._create_tmp_files_dir()
        self._create_tmp_file_names()

        self._init_thread_pool()

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
        for i, link in enumerate(self.data_links):
            encoded = urllib.parse.unquote(link)
            mime = _get_re_group(r'mime=(\w+/\w+)', encoded, 1, 'video/mp4')
            ext = 'webm' if mime == 'audio/webm' else 'mp4'
            self.file_names.append(Path.joinpath(
                self.tmp_files_dir, f'{i}.{ext}'))

    def _init_thread_pool(self):
        self.thread_status = [0] * len(self.data_links)

        self.threads = [threading.Thread(target=self._fetch, args=(link, file_name, i))
                        for i, (link, file_name) in enumerate(
            zip(self.data_links, self.file_names))]

    def _get_content_length(self, link):
        clen_re = r'(?<=(?:\?|&)clen=)(\d+)'
        matches = re.search(clen_re, link)

        if not matches:
            raise UnsupportedURLError(link, 'clen')

        return int(matches.group(0))

    def _gen_chunk_links(self, link):
        clen = self._get_content_length(link)
        range_start = 0
        range_end = self._MAX_CHUNK_SIZE - 1

        range_re = re.compile(r'(?<=(?:\?|&)range=)(\d+-\d+)')
        if not range_re.search(link):
            raise UnsupportedURLError(link, 'range')

        end_found = False

        while not end_found:
            if range_end >= clen:
                range_end = clen - 1
                end_found = True

            # would be more efficient to just find index of it, left for readability
            chunk_link = range_re.sub(f'{range_start}-{range_end}', link)
            yield chunk_link, range_end - range_start + 1
            range_start = range_end + 1
            range_end += self._MAX_CHUNK_SIZE

    def _fetch(self, link, out_file_path, idx):
        """fetches data links in _MAX_CHUNK sizes then merges them"""
        if self.verbose:
            print(f"[{self.title}] Fetching: {link[:150]}...")

        if self.status_obs is not None:
            self.status_obs.dl_started(idx)

        tmp_file_path = f'{out_file_path}_{idx}'

        try:
            with open(out_file_path, 'wb') as f:
                for i, (chunk_link, chunk_size) in enumerate(self._gen_chunk_links(link)):
                    if self.status_obs is not None and not self.status_obs.can_proceed_dl(idx):
                        self.status_obs.dl_finished(idx)
                        # self.status_obs.process_finished(False)
                        # TODO
                        break

                    retried = 0
                    while True:
                        try:
                            with open(tmp_file_path, 'wb') as tmp_f:
                                r = requests.get(chunk_link, stream=True)

                                if not 200 <= r.status_code < 300:
                                    raise ValueError(
                                        f'CHUNK: {i} STATUS: {r.status_code}\n HEADERS: {r.headers}')

                                for chunk in r.raw:
                                    tmp_f.write(chunk)

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
        except UnsupportedURLError as e:
            print(e)
            if self.status_obs is not None:
                self.status_obs.dl_error_occured(idx, type(e), repr(e))
            self.thread_status[idx] = Codes.FETCH_FAILED
            return

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
        IN_FMPEG, OUT_ME = os.pipe()
        if os.fork() == 0:
            os.close(IN_ME)
            os.close(OUT_ME)

            os.close(sys.stderr.fileno())
            os.close(sys.stdin.fileno())

            os.dup2(OUT_FMPEG, sys.stderr.fileno())
            os.dup2(IN_FMPEG, sys.stdin.fileno())

            os.execlp("ffmpeg", "ffmpeg", *files, '-c', 'copy',
                      '-strict', 'experimental', self.path)
        else:
            os.close(OUT_FMPEG)
            os.close(IN_FMPEG)
            # TODO definitely use higher-lvl api lmao
            pattern = '_'.join([str(int.from_bytes(lettr.encode(), "big"))
                                for lettr in '[y/N]'])

            buffer = CircularBuffer(2 * len(pattern))
            while True:
                rd = os.read(IN_ME, 1)
                if rd == b'':
                    break
                full_err_log.append(rd)

                buffer.put(rd)
                if pattern in '_'.join(str(el) for el in buffer.get()):
                    out = 'y' if accept_all_msgs else 'N'
                    # xD
                    os.write(OUT_ME, ord(out).to_bytes(1, "big"))
                    os.write(OUT_ME, ord('\n').to_bytes(1, "big"))
                    buffer.flush()

            os.close(IN_ME)
            os.close(OUT_ME)

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
            total_c_size = sum(self._get_content_length(dl)
                               for dl in self.data_links)

            size = round(total_c_size / 1048576 * 100) / 100  # MB
            t_taken = round((t_end - t_start) * 100) / 100

            print(
                f"[{self.title}] Fetched successfully. SIZE: {size}MB TIME: {t_taken}s")

        if status == Codes.SUCCESS:
            status, err_log = self._merge_tmp_files()
            if self.status_obs is not None:
                self.status_obs.merge_finished(status, err_log)

        if status == Codes.SUCCESS and self.verbose:
            print(f"[{self.title}] OK. Merged successfully.")

        if self.cleanup:
            self._clean_up()

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
