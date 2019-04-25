from aiohttp import web
from bottle import Bottle
from flask import Flask
import marshmallow
from pyramid.config import Configurator
import pytest
from webtest import TestApp

from hapic import Hapic
from hapic import MarshmallowProcessor
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
from hapic.ext.aiohttp.context import AiohttpContext
from hapic.ext.bottle import BottleContext
from hapic.ext.flask import FlaskContext
from hapic.ext.pyramid import PyramidContext
from tests.base import Base


def get_bottle_context():
    h = Hapic(processor_class=MarshmallowProcessor)

    bottle_app = Bottle()
    h.reset_context()
    h.set_context(BottleContext(bottle_app, default_error_builder=MarshmallowDefaultErrorBuilder()))

    class MySchema(marshmallow.Schema):
        name = marshmallow.fields.String(required=True)

    @h.with_api_doc()
    @h.input_body(MySchema())
    def my_controller():
        return {"name": "test"}

    bottle_app.route("/test", method="POST", callback=my_controller)
    return {"hapic": h, "app": bottle_app}


def get_flask_context():
    h = Hapic(processor_class=MarshmallowProcessor)

    flask_app = Flask(__name__)
    h.reset_context()
    h.set_context(FlaskContext(flask_app, default_error_builder=MarshmallowDefaultErrorBuilder()))

    class MySchema(marshmallow.Schema):
        name = marshmallow.fields.String(required=True)

    @h.with_api_doc()
    @h.input_body(MySchema())
    def my_controller():
        return {"name": "test"}

    flask_app.add_url_rule("/test", view_func=my_controller, methods=["POST"])
    return {"hapic": h, "app": flask_app}


def get_pyramid_context():
    h = Hapic(processor_class=MarshmallowProcessor)

    configurator = Configurator(autocommit=True)

    h.reset_context()
    h.set_context(
        PyramidContext(configurator, default_error_builder=MarshmallowDefaultErrorBuilder())
    )

    class MySchema(marshmallow.Schema):
        name = marshmallow.fields.String(required=True)

    @h.with_api_doc()
    @h.input_body(MySchema())
    def my_controller():
        return {"name": "test"}

    configurator.add_route("test", "/test", request_method="POST")
    configurator.add_view(my_controller, route_name="test")
    pyramid_app = configurator.make_wsgi_app()
    return {"hapic": h, "app": pyramid_app}


def get_aiohttp_context():
    h = Hapic(async_=True, processor_class=MarshmallowProcessor)
    aiohttp_app = web.Application(debug=True)
    h.reset_context()
    h.set_context(
        AiohttpContext(aiohttp_app, default_error_builder=MarshmallowDefaultErrorBuilder())
    )

    class MySchema(marshmallow.Schema):
        name = marshmallow.fields.String(required=True)

    @h.with_api_doc()
    @h.input_body(MySchema())
    def my_controller():
        return {"name": "test"}

    aiohttp_app.router.add_post("/", my_controller)

    return {"hapic": h, "app": aiohttp_app}


class TestDocumentationView(Base):
    @pytest.mark.parametrize(
        "context", [get_bottle_context(), get_flask_context(), get_pyramid_context()]
    )
    def test_func__test_documentation_view_ok__all_sync_frameworks(self, context):
        """
        Test documentation view using webtest
        """
        hapic = context["hapic"]
        hapic.add_documentation_view("/doc/", "DOC", "Generated doc")
        app = context["app"]
        app = TestApp(app)

        resp = app.get("/doc/")
        assert resp.status_int == 200
        assert resp.headers.get("Content-Type", "").startswith("text/html")
        assert list(resp.headers)

        resp = app.get("/doc/spec.yml")
        assert resp.status_int == 200
        assert resp.headers.get("Content-Type", "").startswith("text/x-yaml")

    async def test_func__test_documentation_view_ok__aiohttp(self, test_client):
        """
        Test documentation view aiohttp client
        """
        context = get_aiohttp_context()
        hapic = context["hapic"]
        hapic.add_documentation_view("/doc/", "DOC", "Generated doc")
        app = await test_client(context["app"])
        resp = await app.get("/doc/")
        assert resp.status == 200
        assert resp.headers.get("Content-Type", "").startswith("text/html")
        assert list(resp.headers)

        resp = await app.get("/doc/spec.yml")
        assert resp.status == 200
        assert resp.headers.get("Content-Type", "").startswith("text/x-yaml")
