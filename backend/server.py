import asyncio
import websockets
import json
import os
from pathlib import Path

PLAYLIST_FAILED_CODE = 1
PLAYLIST_SUCCEEDED_CODE = 2
DOWNLOADER_SCRIPT_NAME = 'yt_dl.py'
PORT = 5555


playlist = "https://www.youtube.com/watch?v=opgO6h9FIxA&list=PLtjUk3SyYzL5RTjUjk47FH6nCzBo69MMX"
playlist2 = "https://www.youtube.com/watch?v=IlQlKiPgBNk&list=PLmIOcjWlMZTL4qMZGua0xwXbRSSBu-m2r"
playlists = {'playlists': [playlist]}
# playlists = {'playlists': [playlist, playlist2]}
playlist_dir = {
    playlist: 'Gothic_playlist',
    playlist2: 'Stronghold_playlist'
}


def on_links_rcvd(playlist, links):
    playlist_path = Path(__file__).parent.joinpath(playlist_dir[playlist])
    try:
        os.mkdir(playlist_path)
    except FileExistsError as e:
        print(
            f'For playlist {playlist} directory at {playlist_path} already exists')
        # TODO check if all/what was downloaded

    for link_data in links:
        title = link_data['title']
        link = link_data['link']
        sub_link1, sub_link2 = link_data['dataLinks']

        if os.fork() == 0:
            os.execlp('python', DOWNLOADER_SCRIPT_NAME, DOWNLOADER_SCRIPT_NAME,
                      playlist, playlist_path, link, title, sub_link1, sub_link2)
        else:
            # TODO some data structure to add all pids
            # separate thread for waiting? or even this thing in separate thread or even process
            pid, status = os.wait()


def on_msg_rcvd(data):
    playlist = data['playlist']
    code = data['code']

    if code == PLAYLIST_SUCCEEDED_CODE:
        on_links_rcvd(playlist, data['data'])
    else:
        print("ERRRS")
        print(f"FOR Playlist {data['playlist']} got code: {data['code']}")
    # at playlist name (given)
    # create directory
    # for each link spawn worker and download
    # wait for all to finish and run next playlist
    # let every child log progress
    # in case of errors log in file that this item has failed


async def on_connected(ws, path):
    await ws.send(json.dumps(playlists))
    size = len(playlists['playlists'])

    for i in range(size):
        # add timeout in case of failure and send new request then
        #
        links = await ws.recv()
        data = json.loads(links)
        on_msg_rcvd(data)

server = websockets.serve(on_connected, "127.0.0.1", PORT)
print(f'listenning on {PORT}')

asyncio.get_event_loop().run_until_complete(server)
asyncio.get_event_loop().run_forever()
