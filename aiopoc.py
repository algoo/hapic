from sh import tail
from asyncio import sleep
from aiohttp import web


async def handle(request):
    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'text/plain; charset=utf-8',
        },
    )

    await response.prepare(request)
    response.enable_chunked_encoding()

    for line in tail("-f", "aiopocdata.txt", _iter=True):
        await response.write(line.encode('utf-8'))
        await sleep(0.1)

    return response


app = web.Application()
app.add_routes([
    web.get('/', handle)
])


web.run_app(app)
