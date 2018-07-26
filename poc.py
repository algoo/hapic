import asyncio
import aiohttp
import json
from aiohttp import web
import marshmallow
from hapic import async as hapic
from hapic.ext.aiohttp.context import AiohttpContext


class UptimeHandlerStreamItem(marshmallow.Schema):
    datetime = marshmallow.fields.String(required=True)
    a_bool = marshmallow.fields.Boolean(required=True)
    a_float = marshmallow.fields.Number(required=True)
    an_int = marshmallow.fields.Integer(required=True)
    text = marshmallow.fields.String(required=True)
    server = marshmallow.fields.String(required=True)
    zone = marshmallow.fields.String(required=True)


class LineModel(object):
    def __init__(
        self,
        *column_values
    ):
        self.datetime = column_values[0]
        self.a_bool = column_values[1]
        self.a_float = column_values[2]
        self.an_int = column_values[3]
        self.text = column_values[4]
        self.server = column_values[5]
        self.zone = column_values[6]


class AsyncGenerator:
    def __init__(self, session):
        self._session = session
        self._url = 'http://localhost:8086/query?chunk_size=1000&chunked=true'\
                    '&db=resourceAux' \
                    '&q=SELECT+%2A+FROM+resource_aux'
        self._buffer = []
        self._buffer_iter = iter(self._buffer)

    async def __aiter__(self):
        response = await self._session.get(self._url)
        self._stream_reader = response.content
        return self

    async def __anext__(self):
        try:
            try:
                # First, send next item
                return next(self._buffer_iter)
            # If no more item in buffer, or not started
            except StopIteration:
                # Read from incoming data
                line = await self._stream_reader.readline()
                # If end of received lines
                if not line:
                    # Break the iteration
                    raise StopAsyncIteration()

            # load values from received package of incomming data
            data = json.loads(line.decode('utf-8'))
            values = data['results'][0]['series'][0]['values']

            # Prepare new buffer
            self._buffer = [LineModel(*value) for value in values]
            self._buffer_iter = iter(self._buffer)

            # Send an item
            return next(self._buffer_iter)

        except StopAsyncIteration:
            await self._session.close()
            raise


@hapic.with_api_doc()
@hapic.output_stream(item_schema=UptimeHandlerStreamItem())
async def uptime_handler(request):
    try:
        # NOTE: This session is currently closed in AsyncGenerator code
        # it should be made otherwise in real code
        session = aiohttp.ClientSession(loop=loop)
        return AsyncGenerator(session)

    except Exception as e:
        # So you can observe on disconnects and such.
        print(repr(e))
        raise


async def build_server(loop, address, port):
    app = web.Application(loop=loop)
    app.router.add_route('GET', "/uptime", uptime_handler)
    hapic.set_context(AiohttpContext(app))

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
