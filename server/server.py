import asyncio
import websockets
import json
from requests_html import AsyncHTMLSession


# class Prepocessor:
#     def __init__(self):
#         self.playlists = [
#             "https://www.youtube.com/watch?v=opgO6h9FIxA&list=PLtjUk3SyYzL5RTjUjk47FH6nCzBo69MMX"]

#         self.asession = AsyncHTMLSession()

#     async def get_json_playlists(self):
#         data = [{
#             'url': purl,
#             'size': await self._get_playlist_size(purl)
#         } for purl in self.playlists]

#         return json.dumps({'playlists': data})

#     async def _get_playlist_size(self, url):
#         cookies = {'CONSENT': 'YES+PL.pl+20150816-15-0', 'VISITOR_INFO1_LIVE': 'oH8ywplOVLc', 'HSID': 'ACK8uKqXLXcZRuBEF', 'SSID': 'A0B6v1UnJS2So2jU8', 'APISID': 'GiEjOJBPlXqn0MJf/AOQgfs-R-gxb5_Tfh', 'SAPISID': 'hyGZwn8JFGOgvJOP/AVJakpzEJnV9uJFzC', '__Secure-3PAPISID': 'hyGZwn8JFGOgvJOP/AVJakpzEJnV9uJFzC', 'LOGIN_INFO': 'AFmmF2swRAIgXPhEzoJfIPhalCyKbhjOnc2LEzr9-p0aGNxylkCGfuACIHN41m05mqw4eJobluABOzHN4dNUCgEQ5kPRh7XGP8Ga:QUQ3MjNmd09ySUZ3SFZ5OURUUUJwWElaQkFxemFhNHowc1pLVmxickUxT0NQMk1pVlpleDRVSVpjUEk4RGdXeUMxSkNKZy1NWVR2Z3NUQjZaSURMSjdEVEtfYTUtM0FMRGlDM1lITzVvX3ozYWNSWTZFd2FtM1hrSjljcHh5WDNmVEk2TVpneUo4dWxKeExwUkZLWjlVZEdXTW9OZVhqbVpQdUVKSDhqNzJtSnR4dmRGazhEbVl3',
#                    'PREF': 'tz=Europe.Warsaw&f5=20000&hl=en', 'SID': '-werRUhyg5ssGlbXZCLXl2dofAQPspbmc035cUuC2xe1EYYJ3l-mhbDcZdJ_GtdfdYYPPA.', '__Secure-3PSID': '-werRUhyg5ssGlbXZCLXl2dofAQPspbmc035cUuC2xe1EYYJhufIv6PSiwSmRSqhuw0lCA.', 'YSC': '05q1Md_M4A0', 'SIDCC': 'AJi4QfE8UqgXQFNHBeshwJ1ZwSZqY5epD4Kqd4GCW6juBUMTa1l9y7A8gGAOmOW20R8Ulr87MH0', '__Secure-3PSIDCC': 'AJi4QfHnXLZ1fSOSiKEL7O_AGg9dr6KuiLqbxhObj1EsVHuQPpFoVjNrAnpFPP5uYMZfDWSCREc'}

#         resp = await self.asession.get(url, cookies=cookies)
#         html = resp.html.find("body", first=True)
#         with open('tmp.html', 'wb') as f:
#             f.write(html.raw_html)
#         # print(html.raw_html)
#         # html = resp.html.find(
#         #     '#header-contents .ytd-playlist-panel-renderer .index-message', first=True)
#         # print(html.text)


# async def main():
#     preproc = Prepocessor()
#     await preproc.get_json_playlists()

# asyncio.run(main())


PORT = 5555


playlist = "https://www.youtube.com/watch?v=opgO6h9FIxA&list=PLtjUk3SyYzL5RTjUjk47FH6nCzBo69MMX"
playlists = {'playlists': [playlist]}


async def on_connected(ws, path):
    for playlist in playlists:
        await ws.send(json.dumps(playlists))
        links = await(ws.recv())
        print(links)
    print('done.')

server = websockets.serve(on_connected, "127.0.0.1", PORT)
print(f'listenning on {PORT}')

asyncio.get_event_loop().run_until_complete(server)
asyncio.get_event_loop().run_forever()
