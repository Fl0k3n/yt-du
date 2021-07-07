import sys
import os
import requests
import threading
from pathlib import Path
import random

PARENT_DIR = Path(__file__).parent.absolute()
TMP_DIR = Path.joinpath(PARENT_DIR, '.tmp')

FETCH_OK = 1

# DOWNLOADER_SCRIPT_NAME, DOWNLOADER_SCRIPT_NAME,
#                      playlist, playlist_path, link, title, sub_link1, sub_link2)


def fetch(link, out_file_path, status, idx):
    with open(out_file_path, 'wb') as f:
        r = requests.get(link, stream=True)
        for chunk in r.raw:
            f.write(chunk)

    status[idx] = FETCH_OK  # OK


def merge_tmp_files(tmp_file_dir, file_paths, path, title, link):
    files = []
    for f in file_paths:
        files.append('-i')
        files.append(f)

    out_file_name = str(Path.joinpath(Path(path), 'TEST.mp4').absolute())

    if os.fork() == 0:
        os.execlp("ffmpeg", "ffmpeg", *files, '-c', 'copy',
                  '-strict', 'experimental', out_file_name)
    else:
        print(os.wait())


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

    try:
        # increase chance of uniqueness
        tmp_files_dir = Path.joinpath(TMP_DIR, str(
            abs(hash(link))) + f'_{random.randint(1, 10)}')
        os.mkdir(tmp_files_dir)
    except FileExistsError:
        pass

    links = [data_link1, data_link2]
    file_names = [Path.joinpath(
        tmp_files_dir, f'{i}.mp4') for i, _ in enumerate(links)]
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

    # idk assume success
    merge_tmp_files(tmp_files_dir, file_names, path, title, link)

    sys.exit(0)


if __name__ == '__main__':
    main()
