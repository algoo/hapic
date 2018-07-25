import asyncio
import json

from sh import tail
from asyncio import sleep
from aiohttp import web
import marshmallow

from hapic import async as hapic
from hapic.ext.aiohttp.context import AiohttpContext


class OutputStreamItemSchema(marshmallow.Schema):
    i = marshmallow.fields.Integer(required=True)


# Python 3.6 async generator: http://rickyhan.com/jekyll/update/2018/01/27/python36.html
# Python 3.5 solution: https://stackoverflow.com/questions/37549846/how-to-use-yield-inside-async-function


class LinesAsyncGenerator:
    def __init__(self):
        self.iterable = tail("-f", "aiopocdata.txt", _iter=True)

    async def __aiter__(self):
        return self

    async def __anext__(self):
        line = next(self.iterable)

        if 'STOP' in line:
            raise StopAsyncIteration

        await asyncio.sleep(0.025)
        return json.loads(line)


@hapic.with_api_doc()
@hapic.output_stream(item_schema=OutputStreamItemSchema())
def handle(request):
    # response = web.StreamResponse(
    #     status=200,
    #     reason='OK',
    #     headers={
    #         'Content-Type': 'text/plain; charset=utf-8',
    #     },
    # )
    #
    # await response.prepare(request)
    # response.enable_chunked_encoding()

    # for line in tail("-f", "aiopocdata.txt", _iter=True):
        # await response.write(line.encode('utf-8'))
        # await sleep(0.1)

    # return response

    return LinesAsyncGenerator()


app = web.Application()
app.add_routes([
    web.get('/', handle)
])

hapic.set_context(AiohttpContext(app))
web.run_app(app)
