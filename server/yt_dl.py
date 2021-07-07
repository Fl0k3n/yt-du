import sys
import re
import os
import requests
import threading
from pathlib import Path
import urllib
import random

PARENT_DIR = Path(__file__).parent.absolute()
TMP_DIR = Path.joinpath(PARENT_DIR, '.tmp')

FETCH_OK = 1


def fetch(link, out_file_path, status, idx):
    # TODO handle errs
    with open(out_file_path, 'wb') as f:
        r = requests.get(link, stream=True)
        for chunk in r.raw:
            f.write(chunk)

    status[idx] = FETCH_OK


def merge_tmp_files(playlist_idx, tmp_file_dir, file_paths, path, title):
    files = []
    for f in file_paths:
        files.append('-i')
        files.append(f)

    out_file_name = f'{playlist_idx}_{title}.mp4'
    out_full_path = str(Path.joinpath(Path(path), out_file_name).absolute())

    if os.fork() == 0:
        os.close(sys.stderr.fileno())
        os.close(sys.stdout.fileno())
        os.execlp("ffmpeg", "ffmpeg", *files, '-c', 'copy',
                  '-strict', 'experimental', out_full_path)
    else:
        if os.wait() != 0:
            print(f"Failed for {title}")


def _get_re_group(reg, data, idx, default):
    try:
        return re.search(reg, data).group(idx)
    except (AttributeError, IndexError):
        return default


def main():
    if len(sys.argv) != 7:
        print(
            f'USAGE: ./{sys.argv[0]} playlist_name path video_url title data_link1 data_link2',
            file=sys.stderr)
        sys.exit(1)

    playlist, path, link, title, data_link1, data_link2 = sys.argv[1:]

    playlist_idx = _get_re_group(r'index=(\d+)', link, 1, 0)

    try:
        os.mkdir(TMP_DIR)
    except FileExistsError:
        pass

    try:
        # increase chance of uniqueness
        tmp_files_dir = Path.joinpath(TMP_DIR, f'{playlist_idx}_' + str(
            abs(hash(link))) + f'_{random.randint(1, 99)}')
        os.mkdir(tmp_files_dir)
    except FileExistsError:
        pass

    # create tmp files names
    links = [data_link1, data_link2]
    file_names = []
    for i, link in enumerate(links):
        encoded = urllib.parse.unquote(link)
        mime = _get_re_group(r'mime=(\w+/\w+)', encoded, 1, 'video/mp4')
        ext = 'webm' if mime == 'audio/webm' else 'mp4'
        file_names.append(Path.joinpath(tmp_files_dir, f'{i}.{ext}'))

    thread_status = [0] * len(links)

    threads = [threading.Thread(target=fetch, args=(link, file_name, thread_status, i))
               for i, (link, file_name) in enumerate(zip(links, file_names))]

    for thread in threads:
        thread.start()

    # cant zip because not updated data will be generated
    for i, thread in enumerate(threads):
        thread.join()
        if thread_status[i] == FETCH_OK:
            print("OK fetched")
        else:
            print('errs')

    # TODO idk assume success lmao
    merge_tmp_files(playlist_idx, tmp_files_dir, file_names, path, title)

    sys.exit(0)


if __name__ == '__main__':
    main()
