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

path = '/home/flok3n/ytdl/sniacy_zbudz_sie.mp4'

u1 = 'https://r3---sn-x2pm-f5fs.googlevideo.com/videoplayback?expire=1626756501&ei=NQH2YKeOI87vyQXIsYOoBw&ip=185.25.121.191&id=o-AJzDX_zZYc9SyQQ3H0yarN1Nfgj1MoV7fyMApWSTBVbX&itag=137&aitags=133%2C134%2C135%2C136%2C137%2C160%2C242%2C243%2C244%2C247%2C248%2C278%2C394%2C395%2C396%2C397%2C398%2C399&source=youtube&requiressl=yes&mh=Ki&mm=31%2C29&mn=sn-x2pm-f5fs%2Csn-u2oxu-f5fed&ms=au%2Crdu&mv=m&mvi=3&pcm2cms=yes&pl=24&initcwndbps=1578750&vprv=1&mime=video%2Fmp4&ns=F2JXjm2jAK_NJ1cyfXAvEA0G&gir=yes&clen=63174&otfp=1&dur=5.338&lmt=1513571138997598&mt=1626734678&fvip=3&keepalive=yes&fexp=24001373%2C24007246&c=WEB&n=m_oaExrbl0dioA&sparams=expire%2Cei%2Cip%2Cid%2Caitags%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cns%2Cgir%2Cclen%2Cotfp%2Cdur%2Clmt&sig=AOq0QJ8wRQIgGA7ahAnBOurxx6fIh29dQPmDTB-Gr4-0CMPXxugna-kCIQDvUYhXrjg7EyhlTKLv6Apmeu65k-YNXqaBvmNFS_Mr6A%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpcm2cms%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRQIgLBGMUEDPL_b4ZP5Cpi-PqsG1lDneFOH3nRjhpSzTtdwCIQCXIubOpGFasPA7G1teD_WC-D2RTUTWP1gbL9pwWXdvhQ%3D%3D&alr=yes&cpn=RpxmakBrkfdouPKA&cver=2.20210719.00.00&range=0-63173&rn=1&rbuf=0'

u2 = 'https://r3---sn-x2pm-f5fs.googlevideo.com/videoplayback?expire=1626756501&ei=NQH2YKeOI87vyQXIsYOoBw&ip=185.25.121.191&id=o-AJzDX_zZYc9SyQQ3H0yarN1Nfgj1MoV7fyMApWSTBVbX&itag=251&source=youtube&requiressl=yes&mh=Ki&mm=31%2C29&mn=sn-x2pm-f5fs%2Csn-u2oxu-f5fed&ms=au%2Crdu&mv=m&mvi=3&pcm2cms=yes&pl=24&initcwndbps=1578750&vprv=1&mime=audio%2Fwebm&ns=F2JXjm2jAK_NJ1cyfXAvEA0G&gir=yes&clen=74491&otfp=1&dur=5.401&lmt=1565997728186113&mt=1626734678&fvip=3&keepalive=yes&fexp=24001373%2C24007246&c=WEB&n=m_oaExrbl0dioA&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cns%2Cgir%2Cclen%2Cotfp%2Cdur%2Clmt&sig=AOq0QJ8wRAIgBZbm4_muWnLcv2rY7pApiwMCmt501TnnmKEkmTGOuaYCICPPlnlvdmXCiqMBfTckX0HqGWJyNXXsQVgP9s2VUmF2&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpcm2cms%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRQIgLBGMUEDPL_b4ZP5Cpi-PqsG1lDneFOH3nRjhpSzTtdwCIQCXIubOpGFasPA7G1teD_WC-D2RTUTWP1gbL9pwWXdvhQ%3D%3D&alr=yes&cpn=RpxmakBrkfdouPKA&cver=2.20210719.00.00&range=0-65812&rn=2&rbuf=0'


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
