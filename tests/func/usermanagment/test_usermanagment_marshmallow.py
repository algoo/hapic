import pytest
from aiohttp import web
from bottle import Bottle
from flask import Flask
from pyramid.config import Configurator
from webtest import TestApp

from example.usermanagement.userlib import UserLib
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
from hapic.ext.aiohttp.context import AiohttpContext
from hapic.ext.bottle import BottleContext
from hapic.ext.flask import FlaskContext
from hapic.ext.pyramid import PyramidContext


def get_bottle_context():
    from example.usermanagement.serve_bottle_marshmallow import BottleController
    from example.usermanagement.serve_bottle_marshmallow import hapic as h

    bottle_app = Bottle()
    h.reset_context()
    h.set_context(
        BottleContext(
            bottle_app, default_error_builder=MarshmallowDefaultErrorBuilder()
        )
    )
    controllers = BottleController()
    controllers.bind(bottle_app)
    return {"hapic": h, "app": bottle_app}


def get_flask_context():
    from example.usermanagement.serve_flask_marshmallow import FlaskController
    from example.usermanagement.serve_flask_marshmallow import hapic as h

    flask_app = Flask(__name__)
    controllers = FlaskController()
    controllers.bind(flask_app)
    h.reset_context()
    h.set_context(
        FlaskContext(
            flask_app, default_error_builder=MarshmallowDefaultErrorBuilder()
        )
    )
    return {"hapic": h, "app": flask_app}


def get_pyramid_context():
    from example.usermanagement.serve_pyramid_marshmallow import PyramidController
    from example.usermanagement.serve_pyramid_marshmallow import hapic as h

    configurator = Configurator(autocommit=True)
    controllers = PyramidController()
    controllers.bind(configurator)
    h.reset_context()
    h.set_context(
        PyramidContext(
            configurator,
            default_error_builder=MarshmallowDefaultErrorBuilder(),
        )
    )
    pyramid_app = configurator.make_wsgi_app()
    return {"hapic": h, "app": pyramid_app}

def get_aiohttp_context(loop):
    from example.usermanagement.serve_aiohttp_marshmallow import AiohttpController
    from example.usermanagement.serve_aiohttp_marshmallow import hapic as h
    app = web.Application(loop=loop)
    controllers = AiohttpController()
    controllers.bind(app)
    h.reset_context()
    h.set_context(
        AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder())
    )
    return {"hapic": h, "app": app}

@pytest.mark.parametrize(
    "context",
    [get_bottle_context(), get_flask_context(), get_pyramid_context()],
)
def test_func__test_usermanagment_endpoints_ok__sync_frameworks(context):
    UserLib.reset_database()
    hapic = context["hapic"]
    app = context["app"]
    app = TestApp(app)
    resp = app.get("/about")
    assert resp.status_int == 200
    assert resp.json['datetime']
    assert resp.json['version'] == '1.2.3'

    resp = app.get("/users/")
    assert resp.status_int == 200
    assert resp.json == [
        {
            "display_name": "Damien Accorsi",
            "id": 1,
        }
    ]

    resp = app.get("/users/1")
    assert resp.status_int == 200
    assert resp.json == {
        "last_name": "Accorsi",
        "first_name": "Damien",
        "id": 1,
        "display_name": "Damien Accorsi",
        "email_address": "damien.accorsi@algoo.fr",
        "company": "Algoo",
    }

    resp = app.post("/users/", status="*")
    assert resp.status_int == 400
    assert resp.json == {
        "code": None,
        "details": {
            "email_address": ["Missing data for required field."],
            "last_name": ["Missing data for required field."],
            "first_name": ["Missing data for required field."],
        },
        "message": "Validation error of input data",
    }

    user = {
        "email_address": "some.user@hapic.com",
        "last_name": "Accorsi",
        "first_name": "Damien",
        "company": "Algoo",
    }

    resp = app.post_json("/users/", user)
    assert resp.status_int == 200
    assert resp.json == {
        "last_name": "Accorsi",
        "first_name": "Damien",
        "id": 2,
        "email_address": "some.user@hapic.com",
        "company": "Algoo",
        "display_name": "Damien Accorsi",
    }

    resp = app.delete("/users/1", status="*")
    assert resp.status_int == 204
