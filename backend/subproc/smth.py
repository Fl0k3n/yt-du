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

link = 'https://www.youtube.com/watch?v=opgO6h9FIxA&list=PLtjUk3SyYzL5RTjUjk47FH6nCzBo69MMX&index=1'

title = 'Śniący!!! Zbudź się!!!'

playlist_name = 'gothic'

path = '/home/flok3n/dev/pythons/yt-du/server'

u1 = 'https://r3---sn-x2pm-f5fl.googlevideo.com/videoplayback?expire=1625777945&ei=uRLnYMuCLcityAWqxKFA&ip=185.25.121.191&id=o-ANO02kH0dMWC7YQndYl-KC9HXHlhMzVYlCKEhmvUl9s3&itag=399&aitags=133%2C134%2C135%2C136%2C137%2C160%2C242%2C243%2C244%2C247%2C248%2C271%2C278%2C313%2C394%2C395%2C396%2C397%2C398%2C399%2C400%2C401&source=youtube&requiressl=yes&mh=w8&mm=31%2C29&mn=sn-x2pm-f5fl%2Csn-u2oxu-f5fe6&ms=au%2Crdu&mv=m&mvi=3&pl=24&initcwndbps=2311250&vprv=1&mime=video%2Fmp4&ns=zDVRbmqzdaRLiEAcoXRt9g8G&gir=yes&clen=26146741&dur=167.440&lmt=1598961457118132&mt=1625755980&fvip=4&keepalive=yes&fexp=24001373%2C24007246&c=WEB&txp=5531432&n=7aJ1kR7fz6lbeA&sparams=expire%2Cei%2Cip%2Cid%2Caitags%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cns%2Cgir%2Cclen%2Cdur%2Clmt&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRgIhANvynZYopRnQ2xM3a0oagqR5_dX8IT5BL_vk-P0ovwZfAiEArZrNU7_CHjFN6b0oNVzWl-w3I7d38NxGqlH6ja4ZxM4%3D&alr=yes&sig=AOq0QJ8wRgIhAMN3qAzfAbuq5XQJO4QjSB-1cjAOz46WbM7kvOwUd7JVAiEAkbAcmfYL-0JzNvSK2fjrL0pXP7CVuEjvG3f7PA_SdBM%3D&cpn=WymqvN0u7TL83Rrz&cver=2.20210701.07.00&range=0-509174&rn=1&rbuf=0'

u2 = 'https://r3---sn-x2pm-f5fl.googlevideo.com/videoplayback?expire=1625777945&ei=uRLnYMuCLcityAWqxKFA&ip=185.25.121.191&id=o-ANO02kH0dMWC7YQndYl-KC9HXHlhMzVYlCKEhmvUl9s3&itag=251&source=youtube&requiressl=yes&mh=w8&mm=31%2C29&mn=sn-x2pm-f5fl%2Csn-u2oxu-f5fe6&ms=au%2Crdu&mv=m&mvi=3&pl=24&initcwndbps=2311250&vprv=1&mime=audio%2Fwebm&ns=zDVRbmqzdaRLiEAcoXRt9g8G&gir=yes&clen=2835999&dur=167.461&lmt=1596279636831978&mt=1625755980&fvip=4&keepalive=yes&fexp=24001373%2C24007246&c=WEB&txp=5531432&n=7aJ1kR7fz6lbeA&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cns%2Cgir%2Cclen%2Cdur%2Clmt&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRgIhAKImB1Lp-mnvCrG2VUP50XWOp7kJuTzo7zcQAaHqEpnzAiEAz5PJY893SmlDcSE1nidII9urUVpczr_lqpmpryzW2zc%3D&alr=yes&sig=AOq0QJ8wRQIhAMPosBo-RKCh9RgDqgBdXeCFqZTf1TTGiqGB_P-D6e0aAiBFCPcE2OeHISyr6bKM4UtMf0JtinWMEUSpHxWI1A-OSg%3D%3D&cpn=WymqvN0u7TL83Rrz&cver=2.20210701.07.00&range=0-66087&rn=2&rbuf=0'


def _gen_chunk_links(link):
    clen_re = r'(?<=(?:\?|&)clen=)(\d+)'
    matches = re.search(clen_re, u1)
    if not matches:
        raise ValueError('Unsupported url format')

    clen = int(matches.group(0))

    max_chunk_size = 1024

    range_start = 0
    range_end = max_chunk_size-1
    range_re = re.compile(r'(?<=(?:\?|&)range=)(\d+-\d+)')

    if not range_re.search(link):
        raise ValueError('Unsupported url format')

    end_found = False

    while not end_found:
        if range_end >= clen:
            range_end = clen - 1
            end_found = True

        chunk_link = range_re.sub(f'{range_start}-{range_end}', link)
        yield chunk_link
        range_start = range_end + 1
        range_end += max_chunk_size


if os.fork() == 0:
    os.execlp('python', 'python', './yt_dl.py',
              playlist_name, path, link, title, u1, u2)
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