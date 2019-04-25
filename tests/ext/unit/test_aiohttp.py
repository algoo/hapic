# coding: utf-8
from http import HTTPStatus
import io
import json
import sys

from aiohttp import web
from aiohttp.web_request import FileField
from aiohttp.web_request import Request
from aiohttp.web_response import Response
import marshmallow
import pytest

from hapic import Hapic
from hapic import HapicData
from hapic import MarshmallowProcessor
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
from hapic.ext.aiohttp.context import AiohttpContext


class TestAiohttpExt(object):
    async def test_aiohttp_only__ok__nominal_case(self, aiohttp_client, loop):
        async def hello(request):
            return web.Response(text="Hello, world")

        app = web.Application(debug=True)
        app.router.add_get("/", hello)
        client = await aiohttp_client(app)
        resp = await client.get("/")
        assert resp.status == 200
        text = await resp.text()
        assert "Hello, world" in text

    async def test_aiohttp_input_path__ok__nominal_case(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        class InputPathSchema(marshmallow.Schema):
            name = marshmallow.fields.String()

        @hapic.input_path(InputPathSchema())
        async def hello(request, hapic_data: HapicData):
            name = hapic_data.path.get("name")
            return web.Response(text="Hello, {}".format(name))

        app = web.Application(debug=True)
        app.router.add_get("/{name}", hello)
        hapic.set_context(
            AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        )
        client = await aiohttp_client(app)

        resp = await client.get("/bob")
        assert resp.status == 200

        text = await resp.text()
        assert "Hello, bob" in text

    async def test_aiohttp_input_path__error_wrong_input_parameter(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        class InputPathSchema(marshmallow.Schema):
            i = marshmallow.fields.Integer()

        @hapic.input_path(InputPathSchema())
        async def hello(request, hapic_data: HapicData):
            i = hapic_data.path.get("i")
            return web.Response(text="integer: {}".format(str(i)))

        app = web.Application(debug=True)
        app.router.add_get("/{i}", hello)
        hapic.set_context(
            AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        )
        client = await aiohttp_client(app)

        resp = await client.get("/bob")  # NOTE: should be integer here
        assert resp.status == 400

        error = await resp.json()
        assert "Validation error of input data" in error.get("message")
        assert {"i": ["Not a valid integer."]} == error.get("details")

    async def test_aiohttp_input_body__ok_nominal_case(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        class InputBodySchema(marshmallow.Schema):
            name = marshmallow.fields.String()

        @hapic.input_body(InputBodySchema())
        async def hello(request, hapic_data: HapicData):
            name = hapic_data.body.get("name")
            return web.Response(text="Hello, {}".format(name))

        app = web.Application(debug=True)
        app.router.add_post("/", hello)
        hapic.set_context(
            AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        )
        client = await aiohttp_client(app)

        resp = await client.post("/", data={"name": "bob"})
        assert resp.status == 200

        text = await resp.text()
        assert "Hello, bob" in text

    async def test_aiohttp_input_body__error__incorrect_input_body(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        class InputBodySchema(marshmallow.Schema):
            i = marshmallow.fields.Integer()

        @hapic.input_body(InputBodySchema())
        async def hello(request, hapic_data: HapicData):
            i = hapic_data.body.get("i")
            return web.Response(text="integer, {}".format(i))

        app = web.Application(debug=True)
        app.router.add_post("/", hello)
        hapic.set_context(
            AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        )
        client = await aiohttp_client(app)

        resp = await client.post("/", data={"i": "bob"})  # NOTE: should be int
        assert resp.status == 400

        error = await resp.json()
        assert "Validation error of input data" in error.get("message")
        assert {"i": ["Not a valid integer."]} == error.get("details")

    async def test_aiohttp_output_body__ok__nominal_case(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        class OuputBodySchema(marshmallow.Schema):
            name = marshmallow.fields.String()

        @hapic.output_body(OuputBodySchema())
        async def hello(request):
            return {"name": "bob"}

        app = web.Application(debug=True)
        app.router.add_get("/", hello)
        hapic.set_context(
            AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        )
        client = await aiohttp_client(app)

        resp = await client.get("/")
        assert resp.status == 200

        data = await resp.json()
        assert "bob" == data.get("name")

    async def test_aiohttp_output_body__error__incorrect_output_body(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        class OuputBodySchema(marshmallow.Schema):
            i = marshmallow.fields.Integer(required=True)

        @hapic.output_body(OuputBodySchema())
        async def hello(request):
            return {"i": "bob"}  # NOTE: should be integer

        app = web.Application(debug=True)
        app.router.add_get("/", hello)
        hapic.set_context(
            AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        )
        client = await aiohttp_client(app)

        resp = await client.get("/")
        assert resp.status == 500

        data = await resp.text()
        data = await resp.json()
        assert "Validation error of output data" == data.get("message")
        assert {"i": ["Missing data for required field."]} == data.get("details")

    async def test_aiohttp_handle_excpetion__ok__nominal_case(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        @hapic.handle_exception(ZeroDivisionError, http_code=400)
        async def hello(request):
            1 / 0

        app = web.Application(debug=True)
        app.router.add_get("/", hello)
        hapic.set_context(
            AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        )
        client = await aiohttp_client(app)

        resp = await client.get("/")
        assert resp.status == 400

        data = await resp.json()
        assert "division by zero" == data.get("message")

    @pytest.mark.skipif(sys.version_info > (3, 6), reason="requires python3.6 or inferior")
    async def test_aiohttp_output_stream__ok__nominal_case(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        class AsyncGenerator:
            def __init__(self):
                self._iterator = iter([{"name": "Hello, bob"}, {"name": "Hello, franck"}])

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
        app.router.add_get("/", hello)
        hapic.set_context(
            AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        )
        client = await aiohttp_client(app)

        resp = await client.get("/")
        assert resp.status == 200

        line = await resp.content.readline()
        assert b'{"name": "Hello, bob"}\n' == line

        line = await resp.content.readline()
        assert b'{"name": "Hello, franck"}\n' == line

    @pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher")
    async def test_aiohttp_output_stream__ok__py37(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        class OuputStreamItemSchema(marshmallow.Schema):
            name = marshmallow.fields.String()

        from .py37.stream import get_func_with_output_stream

        hello = get_func_with_output_stream(hapic, OuputStreamItemSchema)

        app = web.Application(debug=True)
        app.router.add_get("/", hello)
        hapic.set_context(
            AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        )
        client = await aiohttp_client(app)

        resp = await client.get("/")
        assert resp.status == 200

        line = await resp.content.readline()
        assert b'{"name": "Hello, bob"}\n' == line

        line = await resp.content.readline()
        assert b'{"name": "Hello, franck"}\n' == line

    @pytest.mark.skipif(sys.version_info > (3, 6), reason="requires python3.6 or inferior")
    async def test_aiohttp_output_stream__error__ignore(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        class AsyncGenerator:
            def __init__(self):
                self._iterator = iter(
                    [
                        {"name": "Hello, bob"},
                        {"nameZ": "Hello, Z"},  # This line is incorrect
                        {"name": "Hello, franck"},
                    ]
                )

            async def __aiter__(self):
                return self

            async def __anext__(self):
                return next(self._iterator)

        class OuputStreamItemSchema(marshmallow.Schema):
            name = marshmallow.fields.String(required=True)

        @hapic.output_stream(OuputStreamItemSchema(), ignore_on_error=True)
        async def hello(request):
            return AsyncGenerator()

        app = web.Application(debug=True)
        app.router.add_get("/", hello)
        hapic.set_context(
            AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        )
        client = await aiohttp_client(app)

        resp = await client.get("/")
        assert resp.status == 200

        line = await resp.content.readline()
        assert b'{"name": "Hello, bob"}\n' == line

        line = await resp.content.readline()
        assert b'{"name": "Hello, franck"}\n' == line

    @pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher")
    async def test_aiohttp_output_stream__error__ignore_py37(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        class OuputStreamItemSchema(marshmallow.Schema):
            name = marshmallow.fields.String(required=True)

        from .py37.stream import get_func_with_output_stream_and_error

        hello = get_func_with_output_stream_and_error(hapic, OuputStreamItemSchema)

        app = web.Application(debug=True)
        app.router.add_get("/", hello)
        hapic.set_context(
            AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        )
        client = await aiohttp_client(app)

        resp = await client.get("/")
        assert resp.status == 200

        line = await resp.content.readline()
        assert b'{"name": "Hello, bob"}\n' == line

        line = await resp.content.readline()
        assert b'{"name": "Hello, franck"}\n' == line

    @pytest.mark.skipif(sys.version_info > (3, 6), reason="requires python3.6 or inferior")
    async def test_aiohttp_output_stream__error__interrupt(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        class AsyncGenerator:
            def __init__(self):
                self._iterator = iter(
                    [
                        {"name": "Hello, bob"},
                        {"nameZ": "Hello, Z"},  # This line is incorrect
                        {"name": "Hello, franck"},  # This line must not be reached
                    ]
                )

            async def __aiter__(self):
                return self

            async def __anext__(self):
                return next(self._iterator)

        class OuputStreamItemSchema(marshmallow.Schema):
            name = marshmallow.fields.String(required=True)

        @hapic.output_stream(OuputStreamItemSchema(), ignore_on_error=False)
        async def hello(request):
            return AsyncGenerator()

        app = web.Application(debug=True)
        app.router.add_get("/", hello)
        hapic.set_context(
            AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        )
        client = await aiohttp_client(app)

        resp = await client.get("/")
        assert resp.status == 200

        line = await resp.content.readline()
        assert b'{"name": "Hello, bob"}\n' == line

        line = await resp.content.readline()
        assert b"" == line

    @pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher")
    async def test_aiohttp_output_stream__error__interrupt_py37(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        class OuputStreamItemSchema(marshmallow.Schema):
            name = marshmallow.fields.String(required=True)

        from .py37.stream import get_func_with_output_stream_and_error

        hello = get_func_with_output_stream_and_error(
            hapic, OuputStreamItemSchema, ignore_on_error=False
        )

        app = web.Application(debug=True)
        app.router.add_get("/", hello)
        hapic.set_context(
            AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        )
        client = await aiohttp_client(app)

        resp = await client.get("/")
        assert resp.status == 200

        line = await resp.content.readline()
        assert b'{"name": "Hello, bob"}\n' == line

        line = await resp.content.readline()
        assert b"" == line

    def test_unit__generate_doc__ok__nominal_case(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        class InputPathSchema(marshmallow.Schema):
            username = marshmallow.fields.String(required=True)

        class InputQuerySchema(marshmallow.Schema):
            show_deleted = marshmallow.fields.Boolean(required=False)

        class UserSchema(marshmallow.Schema):
            name = marshmallow.fields.String(required=True)

        @hapic.with_api_doc()
        @hapic.input_path(InputPathSchema())
        @hapic.input_query(InputQuerySchema())
        @hapic.output_body(UserSchema())
        async def get_user(request, hapic_data):
            pass

        @hapic.with_api_doc()
        @hapic.input_path(InputPathSchema())
        @hapic.output_body(UserSchema())
        async def post_user(request, hapic_data):
            pass

        app = web.Application(debug=True)
        app.router.add_get("/{username}", get_user)
        app.router.add_post("/{username}", post_user)
        hapic.set_context(
            AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        )

        doc = hapic.generate_doc("aiohttp", "testing")
        # INFO BS 2019-04-15: Prevent keep of OrderedDict
        doc = json.loads(json.dumps(doc))

        assert "UserSchema" in doc.get("definitions")
        assert {"name": {"type": "string"}} == doc["definitions"]["UserSchema"].get("properties")
        assert "/{username}" in doc.get("paths")
        assert "get" in doc["paths"]["/{username}"]
        assert "post" in doc["paths"]["/{username}"]

        assert [
            {"name": "username", "in": "path", "required": True, "type": "string"},
            {"name": "show_deleted", "in": "query", "required": False, "type": "boolean"},
        ] == doc["paths"]["/{username}"]["get"]["parameters"]
        assert {
            "200": {"schema": {"$ref": "#/definitions/UserSchema"}, "description": "200"}
        } == doc["paths"]["/{username}"]["get"]["responses"]

        assert [{"name": "username", "in": "path", "required": True, "type": "string"}] == doc[
            "paths"
        ]["/{username}"]["post"]["parameters"]
        assert {
            "200": {"schema": {"$ref": "#/definitions/UserSchema"}, "description": "200"}
        } == doc["paths"]["/{username}"]["get"]["responses"]

    def test_unit__generate_output_stream_doc__ok__nominal_case(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        class OuputStreamItemSchema(marshmallow.Schema):
            name = marshmallow.fields.String(required=True)

        @hapic.with_api_doc()
        @hapic.output_stream(OuputStreamItemSchema())
        async def get_users(request, hapic_data):
            pass

        app = web.Application(debug=True)
        app.router.add_get("/", get_users)
        hapic.set_context(
            AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        )

        doc = hapic.generate_doc("aiohttp", "testing")
        # INFO BS 2019-04-15: Prevent keep of OrderedDict
        doc = json.loads(json.dumps(doc))

        assert "/" in doc.get("paths")
        assert "get" in doc["paths"]["/"]
        assert "200" in doc["paths"]["/"]["get"].get("responses", {})
        assert {"items": {"$ref": "#/definitions/OuputStreamItemSchema"}, "type": "array"} == doc[
            "paths"
        ]["/"]["get"]["responses"]["200"]["schema"]

    async def test_unit__general_exception_handling__ok__nominal_case(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        @hapic.with_api_doc()
        async def hello(request):
            return 1 / 0

        app = web.Application(debug=True)
        app.router.add_get("/", hello)
        context = AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        context.handle_exception(ZeroDivisionError, 400)
        hapic.set_context(context)

        client = await aiohttp_client(app)
        resp = await client.get("/")

        json = await resp.json()
        assert resp.status == 400
        assert {
            "details": {"error_detail": {}},
            "message": "division by zero",
            "code": None,
        } == json

    async def test_unit__general_exception_handling__ok__exception_list(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        @hapic.with_api_doc()
        async def zero(request):
            return 1 / 0

        @hapic.with_api_doc()
        async def key(request):
            return dict()["foo"]

        app = web.Application(debug=True)
        app.router.add_get("/a", zero)
        app.router.add_get("/b", key)
        context = AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        context.handle_exceptions([ZeroDivisionError, KeyError], 400)
        hapic.set_context(context)

        client = await aiohttp_client(app)

        resp = await client.get("/a")

        json = await resp.json()
        assert resp.status == 400
        assert {
            "details": {"error_detail": {}},
            "message": "division by zero",
            "code": None,
        } == json
        resp = await client.get("/a")

        json = await resp.json()
        assert resp.status == 400
        assert {
            "details": {"error_detail": {}},
            "message": "division by zero",
            "code": None,
        } == json

    async def test_unit__post_file__ok__put_success(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        class InputFilesSchema(marshmallow.Schema):
            avatar = marshmallow.fields.Raw()

        @hapic.with_api_doc()
        @hapic.input_files(InputFilesSchema())
        async def update_avatar(request: Request, hapic_data: HapicData):
            avatar = hapic_data.files["avatar"]
            assert isinstance(avatar, FileField)
            assert b"text content of file" == avatar.file.read()
            return Response(body="ok")

        app = web.Application(debug=True)
        app.router.add_put("/avatar", update_avatar)
        hapic.set_context(
            AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        )
        client = await aiohttp_client(app)

        resp = await client.put("/avatar", data={"avatar": io.StringIO("text content of file")})
        assert resp.status == 200

    async def test_unit__post_file__ok__missing_file(self, aiohttp_client, loop):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        class InputFilesSchema(marshmallow.Schema):
            avatar = marshmallow.fields.Raw(required=True)

        @hapic.with_api_doc()
        @hapic.input_files(InputFilesSchema())
        async def update_avatar(request: Request, hapic_data: HapicData):
            raise AssertionError("Test should no pass here")

        app = web.Application(debug=True)
        app.router.add_put("/avatar", update_avatar)
        hapic.set_context(
            AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
        )
        client = await aiohttp_client(app)

        resp = await client.put("/avatar")
        assert resp.status == 400
        json_ = await resp.json()
        assert {
            "details": {"avatar": ["Missing data for required field"]},
            "message": "Validation error of input data",
            "code": None,
        } == json_

    async def test_request_header__ok__lowercase_key(self, aiohttp_client):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        class HeadersSchema(marshmallow.Schema):
            foo = marshmallow.fields.String(required=True)

        @hapic.with_api_doc()
        @hapic.input_headers(HeadersSchema())
        async def hello(request, hapic_data: HapicData):
            return web.json_response(hapic_data.headers)

        app = web.Application(debug=True)
        hapic.set_context(AiohttpContext(app))
        app.router.add_get("/", hello)
        client = await aiohttp_client(app)
        response = await client.get("/", headers={"FOO": "bar"})
        assert 200 == response.status
        json_ = await response.json()
        assert {"foo": "bar"} == json_

    async def test_unit__handle_exception__ok__nominal_case(self, aiohttp_client):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        @hapic.with_api_doc()
        @hapic.handle_exception(ZeroDivisionError, http_code=HTTPStatus.BAD_REQUEST)
        def divide_by_zero(request):
            raise ZeroDivisionError()

        app = web.Application(debug=True)
        hapic.set_context(AiohttpContext(app))
        app.router.add_get("/", divide_by_zero)
        client = await aiohttp_client(app)
        response = await client.get("/")

        assert 400 == response.status

    async def test_unit__global_exception__ok__nominal_case(self, aiohttp_client):
        hapic = Hapic(async_=True, processor_class=MarshmallowProcessor)

        @hapic.with_api_doc()
        def divide_by_zero(request):
            raise ZeroDivisionError()

        app = web.Application(debug=True)
        context = AiohttpContext(app)
        hapic.set_context(context)
        context.handle_exception(ZeroDivisionError, http_code=HTTPStatus.BAD_REQUEST)
        app.router.add_get("/", divide_by_zero)
        client = await aiohttp_client(app)
        response = await client.get("/")

        assert 400 == response.status
