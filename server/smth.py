import asyncio
import random


async def produce(name, q):
    print('running')
    for i in range(random.randint(1, 3)):
        await asyncio.sleep(1)
        await q.put((name, i))
        print(f'{name} put {i}')


async def consume(name, q):
    while True:
        await asyncio.sleep(0.5)
        prod, i = await q.get()
        q.task_done()
        print(f'{name} consumed {i} from {prod}')


async def main():
    q = asyncio.Queue()
    # producers = [asyncio.create_task(produce(n, q)) for n in range(3)]
    producers = [produce(n, q) for n in range(3)]
    consumers = [asyncio.create_task(consume(n, q)) for n in range(3)]
    await asyncio.gather(*producers)
    # print(q.qsize())

# asyncio.run(main())


async def msger():
    await asyncio.sleep(0.5)
    return 1


async def itter():
    tasks = [await msger() for i in range(3)]
    async for t in tasks:
        print(t)

asyncio.run(itter())

# asyncio.get_event_loop().run_until_complete(do_smth())
# asyncio.get_event_loop().run_forever()
