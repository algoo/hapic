import asyncio
import aiohttp
import json
from aiohttp import web


async def uptime_handler(request):
    resp = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename="filename.csv"',
        }
    )
    await resp.prepare(request)

    try:
        async with aiohttp.ClientSession(loop=loop) as session:
            url = 'http://localhost:8086/query?chunk_size=1000&chunked=true&db=resourceAux&q=SELECT+%2A+FROM+resource_aux'  # nopep8
            async with session.get(url) as response:
                async for chunk in response.content:
                    bytes_to_str = chunk.decode('utf-8')
                    result = json.loads(bytes_to_str)['results'][0]['series'][0]['values']  # nopep8
                    for r in result:
                        await resp.write(str.encode(str(r)+'\n'))

    except Exception as e:
        # So you can observe on disconnects and such.
        print(repr(e))
        raise

    return resp


async def build_server(loop, address, port):
    app = web.Application(loop=loop)
    app.router.add_route('GET', "/uptime", uptime_handler)

    return await loop.create_server(app.make_handler(), address, port)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(build_server(loop, 'localhost', 9999))
    print("Server ready!")

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Shutting Down!")
        loop.close()
