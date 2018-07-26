# coding: utf-8
from aiohttp import web
import marshmallow

from hapic import Hapic
from hapic import HapicData
from hapic.ext.aiohttp.context import AiohttpContext


class TestAiohttpExt(object):
    async def test_aiohttp_only__ok__nominal_case(
        self,
        aiohttp_client,
        loop,
    ):
        async def hello(request):
            return web.Response(text='Hello, world')

        app = web.Application(debug=True)
        app.router.add_get('/', hello)
        client = await aiohttp_client(app)
        resp = await client.get('/')
        assert resp.status == 200
        text = await resp.text()
        assert 'Hello, world' in text

    async def test_aiohttp_input_path__ok__nominal_case(
        self,
        aiohttp_client,
        loop,
    ):
        hapic = Hapic(async_=True)

        class InputPathSchema(marshmallow.Schema):
            name = marshmallow.fields.String()

        @hapic.input_path(InputPathSchema())
        async def hello(request, hapic_data: HapicData):
            name = hapic_data.path.get('name')
            return web.Response(text='Hello, {}'.format(name))

        app = web.Application(debug=True)
        app.router.add_get('/{name}', hello)
        hapic.set_context(AiohttpContext(app))
        client = await aiohttp_client(app)

        resp = await client.get('/bob')
        assert resp.status == 200

        text = await resp.text()
        assert 'Hello, bob' in text

    async def test_aiohttp_input_path__error_wrong_input_parameter(
        self,
        aiohttp_client,
        loop,
    ):
        hapic = Hapic(async_=True)

        class InputPathSchema(marshmallow.Schema):
            i = marshmallow.fields.Integer()

        @hapic.input_path(InputPathSchema())
        async def hello(request, hapic_data: HapicData):
            i = hapic_data.path.get('i')
            return web.Response(text='integer: {}'.format(str(i)))

        app = web.Application(debug=True)
        app.router.add_get('/{i}', hello)
        hapic.set_context(AiohttpContext(app))
        client = await aiohttp_client(app)

        resp = await client.get('/bob')  # NOTE: should be integer here
        assert resp.status == 400

        error = await resp.json()
        assert 'Validation error of input data' in error.get('message')
        assert {'i': ['Not a valid integer.']} == error.get('details')

    async def test_aiohttp_input_body__ok_nominal_case(
        self,
        aiohttp_client,
        loop,
    ):
        hapic = Hapic(async_=True)

        class InputBodySchema(marshmallow.Schema):
            name = marshmallow.fields.String()

        @hapic.input_body(InputBodySchema())
        async def hello(request, hapic_data: HapicData):
            name = hapic_data.body.get('name')
            return web.Response(text='Hello, {}'.format(name))

        app = web.Application(debug=True)
        app.router.add_post('/', hello)
        hapic.set_context(AiohttpContext(app))
        client = await aiohttp_client(app)

        resp = await client.post('/', data={'name': 'bob'})
        assert resp.status == 200

        text = await resp.text()
        assert 'Hello, bob' in text

    async def test_aiohttp_input_body__error__incorrect_input_body(
        self,
        aiohttp_client,
        loop,
    ):
        hapic = Hapic(async_=True)

        class InputBodySchema(marshmallow.Schema):
            i = marshmallow.fields.Integer()

        @hapic.input_body(InputBodySchema())
        async def hello(request, hapic_data: HapicData):
            i = hapic_data.body.get('i')
            return web.Response(text='integer, {}'.format(i))

        app = web.Application(debug=True)
        app.router.add_post('/', hello)
        hapic.set_context(AiohttpContext(app))
        client = await aiohttp_client(app)

        resp = await client.post('/', data={'i': 'bob'})  # NOTE: should be int
        assert resp.status == 400

        error = await resp.json()
        assert 'Validation error of input data' in error.get('message')
        assert {'i': ['Not a valid integer.']} == error.get('details')

    async def test_aiohttp_output_body__ok__nominal_case(
        self,
        aiohttp_client,
        loop,
    ):
        hapic = Hapic(async_=True)

        class OuputBodySchema(marshmallow.Schema):
            name = marshmallow.fields.String()

        @hapic.output_body(OuputBodySchema())
        async def hello(request):
            return {
                'name': 'bob',
            }

        app = web.Application(debug=True)
        app.router.add_get('/', hello)
        hapic.set_context(AiohttpContext(app))
        client = await aiohttp_client(app)

        resp = await client.get('/')
        assert resp.status == 200

        data = await resp.json()
        assert 'bob' == data.get('name')

    async def test_aiohttp_output_body__error__incorrect_output_body(
        self,
        aiohttp_client,
        loop,
    ):
        hapic = Hapic(async_=True)

        class OuputBodySchema(marshmallow.Schema):
            i = marshmallow.fields.Integer(required=True)

        @hapic.output_body(OuputBodySchema())
        async def hello(request):
            return {
                'i': 'bob',  # NOTE: should be integer
            }

        app = web.Application(debug=True)
        app.router.add_get('/', hello)
        hapic.set_context(AiohttpContext(app))
        client = await aiohttp_client(app)

        resp = await client.get('/')
        assert resp.status == 500

        data = await resp.json()
        assert 'Validation error of output data' == data.get('message')
        assert {
                   'i': ['Missing data for required field.'],
               } == data.get('details')

    async def test_aiohttp_output_stream__ok__nominal_case(
        self,
        aiohttp_client,
        loop,
    ):
        hapic = Hapic(async_=True)

        class AsyncGenerator:
            def __init__(self):
                self._iterator = iter([
                    {'name': 'Hello, bob'},
                    {'name': 'Hello, franck'},
                ])

            async def __aiter__(self):
                return self

            async def __anext__(self):
                return next(self._iterator)

        class OuputStreamItemSchema(marshmallow.Schema):
            name = marshmallow.fields.String()

        @hapic.output_stream(OuputStreamItemSchema())
        async def hello(request):
            return AsyncGenerator()

        app = web.Application(debug=True)
        app.router.add_get('/', hello)
        hapic.set_context(AiohttpContext(app))
        client = await aiohttp_client(app)

        resp = await client.get('/')
        assert resp.status == 200

        line = await resp.content.readline()
        assert b'{"name": "Hello, bob"}\n' == line

        line = await resp.content.readline()
        assert b'{"name": "Hello, franck"}\n' == line

        # TODO BS 2018-07-26: How to ensure we are at end of response ?
