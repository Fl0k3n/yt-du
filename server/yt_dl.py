import sys
import re
import os
import requests
import threading
from pathlib import Path
import urllib
import random
from enum import Enum

PARENT_DIR = Path(__file__).parent.absolute()
TMP_DIR = Path.joinpath(PARENT_DIR, '.tmp')


def _get_re_group(reg, data, idx, default):
    try:
        return re.search(reg, data).group(idx)
    except (AttributeError, IndexError):
        return default


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
    def __init__(self, playlist, path, link, title, data_links, retries=3, verbose=True):
        """
        Args:
            playlist (string): playlist url
            path (string): absolute path to directory where downloaded video should be saved
            link (string): url to video to download
            title (string): title of video
            data_links ([string]): array of data links, for now each video should have 2 (audio.webm + video.mp4)
            retries (int): how many times download should be retried
        """
        self.playlist = playlist
        self.path = path
        self.link = link
        self.title = title
        self.data_links = data_links
        self.retries = retries
        self.verbose = verbose

        self.playlist_idx = _get_re_group(r'index=(\d+)', link, 1, 0)

        self._create_tmp_files_dir()
        self._create_tmp_file_names()

        self._init_thread_pool()

    def _create_tmp_files_dir(self):
        try:
            # increase chance of uniqueness
            self.tmp_files_dir = Path.joinpath(TMP_DIR, f'{self.playlist_idx}_' + str(
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
                        for i, (link, file_name) in enumerate(zip(self.data_links, self.file_names))]

    def _fetch(self, link, out_file_path, idx):
        if self.verbose:
            print(f"[{self.title}] Fetching: {link[:150]}...")

        # TODO persistent retries?
        retried = 0
        while True:
            try:
                with open(out_file_path, 'wb') as f:
                    r = requests.get(link, stream=True)

                    if not 200 <= r.status_code < 300:
                        raise ValueError(
                            f'Request code was {r.status_code}\n HEADERS: {r.headers}')

                    for chunk in r.raw:
                        f.write(chunk)

                self.thread_status[idx] = Codes.SUCCESS
                break
            except Exception as e:
                print("Failed to fetch.")
                print(type(e), e)

                if retried == self.retries:
                    self.thread_status[idx] = Codes.FETCH_FAILED
                    break
                retried += 1

    def _merge_tmp_files(self, accept_all_msgs=True):
        if self.verbose:
            print(f'[{self.title}] Merging.')

        files = []
        for f in self.file_names:
            files.append('-i')
            files.append(f)

        out_file_name = f'{self.playlist_idx}_{self.title}.mp4'
        out_full_path = str(Path.joinpath(
            Path(self.path), out_file_name).absolute())

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
                      '-strict', 'experimental', out_full_path)
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
        def try_del(name, func):
            try:
                func(name)
            except Exception as e:
                print("Failed to cleanup.")
                print(type(e), e)

        for fname in self.file_names:
            try_del(fname, lambda x: os.remove(x))

        for dname in [self.tmp_files_dir]:
            try_del(dname, lambda x: os.rmdir(x))

    def download(self):
        for thread in self.threads:
            thread.start()

        status = Codes.SUCCESS  # no errors yet

        # cant zip because not updated data might be generated
        for i, thread in enumerate(self.threads):
            thread.join()
            if self.thread_status[i] != Codes.SUCCESS:
                status = self.thread_status[i]
                print(
                    f"Aborting, failed to download {self.title}\n{self.data_links[i]}")
                break

        if status == Codes.SUCCESS:
            status, err_log = self._merge_tmp_files()

        self._clean_up()
        return status, err_log


def main():
    if len(sys.argv) != 7:
        print(
            f'USAGE: ./{sys.argv[0]} playlist_name path video_url title data_link1 data_link2',
            file=sys.stderr)
        sys.exit(1)

    playlist, path, link, title, data_link1, data_link2 = sys.argv[1:]

    try:
        os.mkdir(TMP_DIR)
    except FileExistsError:
        pass

    ytdl = YTDownloader(playlist, path, link, title, [
                        data_link1, data_link2], verbose=False)
    status, err_log = ytdl.download()

    if status != Codes.SUCCESS:
        print('-'*20 + 'FAILED TO DOWNLOAD' + '-'*20)
        print(err_log)
    else:
        print(f'OK [{title}] downloaded successfully')

    sys.exit(0)


if __name__ == '__main__':
    main()
