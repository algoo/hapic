from aiohttp import web
from bottle import Bottle
from flask import Flask
import marshmallow
from pyramid.config import Configurator

from hapic import Hapic
from hapic import MarshmallowProcessor
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
from hapic.ext.aiohttp.context import AiohttpContext
from hapic.ext.bottle import BottleContext
from hapic.ext.flask import FlaskContext
from hapic.ext.pyramid import PyramidContext


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
