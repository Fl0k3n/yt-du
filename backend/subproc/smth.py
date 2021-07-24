from queue import Queue, Empty
import time
import threading
from pprint import pprint
import requests
import pathlib
import os
import sys
import asyncio
import random
import re


# async def produce(name, q):
#     print('running')
#     for i in range(random.randint(1, 3)):
#         await asyncio.sleep(1)
#         await q.put((name, i))
#         print(f'{name} put {i}')


# async def consume(name, q):
#     while True:
#         await asyncio.sleep(0.5)
#         prod, i = await q.get()
#         q.task_done()
#         print(f'{name} consumed {i} from {prod}')


# async def main():
#     q = asyncio.Queue()
#     # producers = [asyncio.create_task(produce(n, q)) for n in range(3)]
#     producers = [produce(n, q) for n in range(3)]
#     consumers = [asyncio.create_task(consume(n, q)) for n in range(3)]
#     await asyncio.gather(*producers)
#     # print(q.qsize())

# # asyncio.run(main())


# async def msger():
#     await asyncio.sleep(0.5)
#     return 1


# async def itter():
#     tasks = [await msger() for i in range(3)]
#     async for t in tasks:
#         print(t)

# asyncio.run(itter())

# # asyncio.get_event_loop().run_until_complete(do_smth())
# # asyncio.get_event_loop().run_forever()


# import os
# import multiprocessing

# type 1 urls(clen)
link = 'https://www.youtube.com/watch?v=opgO6h9FIxA&list=PLtjUk3SyYzL5RTjUjk47FH6nCzBo69MMX&index=1'

title = 'Śniący!!! Zbudź się!!!'

playlist_name = 'gothic'

path = '/home/flok3n/ytdl/sniacy_zbudz_sie.mp4'

u1 = 'https://r3---sn-x2pm-f5fs.googlevideo.com/videoplayback?expire=1627154326&ei=NhP8YNn3KdOHyAXOsIrYBw&ip=185.25.121.191&id=o-AMMfD6Z9P4o1357Fqm6UPE4_R_zpoP7JEZeUbWU9vRZF&itag=137&aitags=133%2C134%2C135%2C136%2C137%2C160%2C242%2C243%2C244%2C247%2C248%2C278%2C394%2C395%2C396%2C397%2C398%2C399&source=youtube&requiressl=yes&mh=Ki&mm=31%2C29&mn=sn-x2pm-f5fs%2Csn-u2oxu-f5fed&ms=au%2Crdu&mv=m&mvi=3&pl=24&initcwndbps=1238750&vprv=1&mime=video%2Fmp4&ns=9SALP-vIXdwiZBOEJ_uenkUG&gir=yes&clen=63174&otfp=1&dur=5.338&lmt=1513571138997598&mt=1627132601&fvip=3&keepalive=yes&fexp=24001373%2C24007246&c=WEB&n=jBitNXlMjyKN2g&sparams=expire%2Cei%2Cip%2Cid%2Caitags%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cns%2Cgir%2Cclen%2Cotfp%2Cdur%2Clmt&sig=AOq0QJ8wRQIhAO7RljeLDY7tdMqcejkMwJrZG4GGv1xDZdikgCTEzSClAiB7QxSKPod0KSssa1wKs32qNVE4yn0P4gCpi_sboblN_w%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRgIhAKF5Gdro6NpGWEaKf6eK204xdnEea4T9h0zFQoei_otiAiEAoo5JVjER07S-wh633So3u6ntMFM5vNK8Y4QKuNx3hl4%3D&alr=yes&cpn=CwQkoqaiTCAU8nkA&cver=2.20210721.00.00&range=0-63173&rn=1&rbuf=0'

u2 = 'https://r3---sn-x2pm-f5fs.googlevideo.com/videoplayback?expire=1627154326&ei=NhP8YNn3KdOHyAXOsIrYBw&ip=185.25.121.191&id=o-AMMfD6Z9P4o1357Fqm6UPE4_R_zpoP7JEZeUbWU9vRZF&itag=251&source=youtube&requiressl=yes&mh=Ki&mm=31%2C29&mn=sn-x2pm-f5fs%2Csn-u2oxu-f5fed&ms=au%2Crdu&mv=m&mvi=3&pl=24&initcwndbps=1238750&vprv=1&mime=audio%2Fwebm&ns=9SALP-vIXdwiZBOEJ_uenkUG&gir=yes&clen=74491&otfp=1&dur=5.401&lmt=1565997728186113&mt=1627132601&fvip=3&keepalive=yes&fexp=24001373%2C24007246&c=WEB&n=jBitNXlMjyKN2g&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cns%2Cgir%2Cclen%2Cotfp%2Cdur%2Clmt&sig=AOq0QJ8wRgIhAMD4GAZhVjVtddVSN1fdOoVxGUCHiRuMzLzeudSlWf5AAiEA0pdrVTH_7kYemN-QvFvv0p1OgMsEc7fNEuvgod7N18o%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRgIhAKF5Gdro6NpGWEaKf6eK204xdnEea4T9h0zFQoei_otiAiEAoo5JVjER07S-wh633So3u6ntMFM5vNK8Y4QKuNx3hl4%3D&alr=yes&cpn=CwQkoqaiTCAU8nkA&cver=2.20210721.00.00&range=0-65812&rn=2&rbuf=0'


# type 2 urls(sq)
# link = 'https://www.youtube.com/watch?v=wwRfa0cPY-0&list=PLUhmme4GQ9xonblEQQJRLyQzXzmafS_nj&index=9'

# title = 'Asap Rocky - Keep It G'

# playlist_name = 'live love asap'

# path = '/home/flok3n/ytdl/asap_rocky_keep_it_g.mp4'

# u1 = 'https://r6---sn-x2pm-f5fs.googlevideo.com/videoplayback?expire=1627084195&ei=QwH7YJPQBoyBpASBoJPQCA&ip=185.25.121.191&id=o-AMYdcY3wn_KBw4cDpYPszKBjPt3r9kUBhW1VqTNnf3a9&itag=135&aitags=133%2C134%2C135%2C160%2C242%2C243%2C244%2C278&source=yt_otf&requiressl=yes&mh=YV&mm=31%2C29&mn=sn-x2pm-f5fs%2Csn-u2oxu-f5fek&ms=au%2Crdu&mv=m&mvi=6&pl=24&initcwndbps=1140000&vprv=1&mime=video%2Fmp4&ns=cfm3ekAXAvuW_amRt5MHIOwG&otf=1&otfp=1&dur=0.000&lmt=1480857666340217&mt=1627062527&fvip=1&keepalive=yes&fexp=24001373%2C24007246&c=WEB&n=Ck_xblxAIGKUnA&sparams=expire%2Cei%2Cip%2Cid%2Caitags%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cns%2Cotf%2Cotfp%2Cdur%2Clmt&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRgIhAL9W4asUpfhePOxLAldnzMYiSc_e1XMT7si0eyZ3B7FJAiEAqpBDzEeS--e9tW8u7nxwzaBjB4FS_6DTmqNLF4oBTMA%3D&alr=yes&sig=AOq0QJ8wRQIgIhPyLdVr7UuiJKK4AMR-eUqD8rY0A6PJVI78ncsNRzoCIQDxKVYLGTUY5KRlJp310c3wNXvZ-N1yBGkvl6AYJ4JYbA%3D%3D&cpn=cJwa-gcELhMk1aTv&cver=2.20210721.00.00&sq=0&rn=1&rbuf=0'

# u2 = 'https://r6---sn-x2pm-f5fs.googlevideo.com/videoplayback?expire=1627084195&ei=QwH7YJPQBoyBpASBoJPQCA&ip=185.25.121.191&id=o-AMYdcY3wn_KBw4cDpYPszKBjPt3r9kUBhW1VqTNnf3a9&itag=251&source=youtube&requiressl=yes&mh=YV&mm=31%2C29&mn=sn-x2pm-f5fs%2Csn-u2oxu-f5fek&ms=au%2Crdu&mv=m&mvi=6&pl=24&initcwndbps=1140000&vprv=1&mime=audio%2Fwebm&ns=cfm3ekAXAvuW_amRt5MHIOwG&gir=yes&clen=2899505&otfp=1&dur=182.141&lmt=1563867798213303&mt=1627062527&fvip=1&keepalive=yes&fexp=24001373%2C24007246&c=WEB&n=Ck_xblxAIGKUnA&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cns%2Cgir%2Cclen%2Cotfp%2Cdur%2Clmt&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRQIgUm1BttH0lEr19PxwdiuEgMFayxeIOIV2Tq9Lt0vj1IICIQCMC7i7O6f9Vi-K-EWr5zqpfLO-yy47CMBU7rKbpGFnuA%3D%3D&alr=yes&sig=AOq0QJ8wRQIgSN6FjSNmANcqFbhdeBHpW51Pg6H7_mLarjKumGhaAFMCIQD1ae2uDMLP-CCDuerMLtmUuPKfrxWhG9qg3gwOK3V9Dw%3D%3D&cpn=cJwa-gcELhMk1aTv&cver=2.20210721.00.00&range=0-66114&rn=2&rbuf=0'


if os.fork() == 0:
    os.execlp('python', 'python', './yt_dl.py',
              path, link, title, u1, u2)
else:
    print(os.wait())


# with open('out.mp4', 'wb') as f:
#     r = requests.get(url, stream=True)
#     for data in r.raw:
#         f.write(data)

# u5 = 'https://r3---sn-x2pm-f5fs.googlevideo.com/videoplayback?expire=1625687787&ei=i7LlYJagEsS9yAWmhaXwDg&ip=185.25.121.191&id=o-ABahoSCnCUMXTjOUhY2Oj1rj1UAyB2RVBpR5gntEPdH1&itag=137&aitags=133%2C134%2C135%2C136%2C137%2C160%2C242%2C243%2C244%2C247%2C248%2C278%2C394%2C395%2C396%2C397%2C398%2C399&source=youtube&requiressl=yes&mh=Ki&mm=31%2C29&mn=sn-x2pm-f5fs%2Csn-u2oxu-f5fed&ms=au%2Crdu&mv=m&mvi=3&pl=24&initcwndbps=1430000&vprv=1&mime=video%2Fmp4&ns=BcLoNbmLPf-lB6DF9lQ2iaQG&gir=yes&clen=63174&otfp=1&dur=5.338&lmt=1513571138997598&mt=1625665969&fvip=3&keepalive=yes&fexp=24001373%2C24007246&c=WEB&n=UEx7eMPd-aNC9A&sparams=expire%2Cei%2Cip%2Cid%2Caitags%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cns%2Cgir%2Cclen%2Cotfp%2Cdur%2Clmt&sig=AOq0QJ8wRQIgYJynsa7JHjPObiTqncly6B-X7RGjzZuf7_Zt_fEN1ZICIQDJI2zu7sgBXl7mq06fUEqGtNRLCbc7fx60YHWpku7KJw%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRQIgRmu-66WneiUVX8-2YjI2JG9yrUQtYNOa8STx4oUrI8oCIQCWCX3XA2ErHDYL5hcF7Eumf48kZVlIiKYY3nj3kxlZEA%3D%3D&alr=yes&cpn=PFG3NZSKz7Z2XvPU&cver=2.20210701.07.00&range=0-63173&rn=1&rbuf=0'


# r = requests.get(u1)
# pprint(r.headers)
# pprint(r.status_code)

# t2_url = 'https://r6---sn-x2pm-f5fs.googlevideo.com/videoplayback?expire=1627067155&ei=sr76YNvSOdXWyQWD6ofYCw&ip=185.25.121.191&id=o-ACU8i4GSks1YTq4VLKBpQ8OrUmiNqIrxBjEHzq8511CH&itag=135&aitags=133%2C134%2C135%2C160%2C242%2C243%2C244%2C278&source=yt_otf&requiressl=yes&mh=YV&mm=31%2C29&mn=sn-x2pm-f5fs%2Csn-u2oxu-f5fek&ms=au%2Crdu&mv=m&mvi=6&pl=24&initcwndbps=1415000&vprv=1&mime=video%2Fmp4&ns=pZ6KS-46thYZfqWHmJE9OuYG&otf=1&otfp=1&dur=0.000&lmt=1480857666340217&mt=1627045254&fvip=1&keepalive=yes&fexp=24001373%2C24007246&c=WEB&n=Q1G5m63zPxJShw&sparams=expire%2Cei%2Cip%2Cid%2Caitags%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cns%2Cotf%2Cotfp%2Cdur%2Clmt&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRQIhAKesu1RO61XRpuKCvHVzOSW1d8lbAJIdEuob8H1tNuWYAiAgBZ1D9GudlCzh8LeS3xq5CMhjVIVP3Re_H8MimZfCfQ%3D%3D&alr=yes&sig=AOq0QJ8wRQIhAOMZIBa1p91KoQKh87PCaLh5_7Nkhy_N79APkwtxH64HAiA36LjF3JfL5w63muPKWJ7lNAQca74a9eLj0HB7FhIEgg%3D%3D&cpn=HMIEkbSZlgdAaZFf&cver=2.20210721.00.00&sq=0&rn=1&rbuf=0'


# class PH:
#     _MAX_SIZE_FETCHING_THREADS = 10

#     def __init__(self, url):
#         self.url = url
#         self.seg_count = 38

#     def _init_size_thread_pool(self):
#         self.task_queue = Queue()
#         self.threads = []

#         for i, url in enumerate(self._generate_chunk_urls()):
#             self.task_queue.put((i, url))

#         for i in range(min(self._MAX_SIZE_FETCHING_THREADS, self._get_seg_count())):
#             self.threads.append(threading.Thread(
#                 target=self._fetch_content_len))

#         self.seg_sizes = [None] * self._get_seg_count()

#     def _get_seg_count(self) -> int:
#         if self.seg_count is None:
#             resp = requests.get(self.url)
#             seg_re = r'Segment-Count: (\d+)'
#             self.seg_count = int(re.search(seg_re, resp.text).group(1)) + 1

#         return self.seg_count

#     def _generate_chunk_urls(self):
#         seg_re = r'(?<=\?|&)(sq=(\d+))'
#         matches = re.search(seg_re, self.url)

#         url_pref = self.url[:matches.start(1)]
#         url_suff = self.url[matches.end(1):]

#         for i in range(self._get_seg_count()):
#             yield f'{url_pref}sq={i}{url_suff}'

#     def _fetch_content_len(self):
#         while True:
#             try:
#                 idx, url = self.task_queue.get(block=False)
#                 self.seg_sizes[idx] = int(
#                     requests.head(url).headers['Content-Length'])
#             except Empty:
#                 return

#     def get_size(self):
#         self._init_size_thread_pool()
#         for thread in self.threads:
#             thread.start()

#         for thread in self.threads:
#             thread.join()

#         return sum(self.seg_sizes)


# x = PH(t2_url)
# start = time.time()
# print(x.get_size())
# print(f'{time.time() - start}s')
