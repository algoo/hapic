import json

from aiohttp import web
from bottle import Bottle
from flask import Flask
from pyramid.config import Configurator
import pytest
from webtest import TestApp

from example.usermanagement.userlib import UserLib
from hapic.error.serpyco import SerpycoDefaultErrorBuilder
from hapic.ext.aiohttp.context import AiohttpContext
from hapic.ext.bottle import BottleContext
from hapic.ext.flask import FlaskContext
from hapic.ext.pyramid import PyramidContext


def get_bottle_context():
    from example.usermanagement.serve_bottle_serpyco import BottleController
    from example.usermanagement.serve_bottle_serpyco import hapic as h

    bottle_app = Bottle()
    h.reset_context()
    h.set_context(BottleContext(bottle_app, default_error_builder=SerpycoDefaultErrorBuilder()))
    controllers = BottleController()
    controllers.bind(bottle_app)
    return {"hapic": h, "app": bottle_app}


def get_flask_context():
    from example.usermanagement.serve_flask_serpyco import FlaskController
    from example.usermanagement.serve_flask_serpyco import hapic as h

    flask_app = Flask(__name__)
    controllers = FlaskController()
    controllers.bind(flask_app)
    h.reset_context()
    h.set_context(FlaskContext(flask_app, default_error_builder=SerpycoDefaultErrorBuilder()))
    return {"hapic": h, "app": flask_app}


def get_pyramid_context():
    from example.usermanagement.serve_pyramid_serpyco import PyramidController
    from example.usermanagement.serve_pyramid_serpyco import hapic as h

    configurator = Configurator(autocommit=True)
    controllers = PyramidController()
    controllers.bind(configurator)
    h.reset_context()
    h.set_context(PyramidContext(configurator, default_error_builder=SerpycoDefaultErrorBuilder()))
    pyramid_app = configurator.make_wsgi_app()
    return {"hapic": h, "app": pyramid_app}


def get_aiohttp_app(loop):
    from example.usermanagement.serve_aiohttp_serpyco import AiohttpController

    controllers = AiohttpController()
    app = web.Application(loop=loop)
    controllers.bind(app)
    return app


def get_aiohttp_context(loop):
    from example.usermanagement.serve_aiohttp_serpyco import hapic as h

    h.reset_context()
    app = get_aiohttp_app(loop)
    h.set_context(AiohttpContext(app, default_error_builder=SerpycoDefaultErrorBuilder()))
    return {"hapic": h, "app": app}


@pytest.mark.parametrize(
    "context", [get_bottle_context(), get_flask_context(), get_pyramid_context()]
)
def test_func__test_usermanagment_endpoints_ok__sync_frameworks(context):
    UserLib.reset_database()
    app = context["app"]
    app = TestApp(app)
    resp = app.get("/about")
    assert resp.status_int == 200
    assert resp.json["datetime"]
    assert resp.json["version"] == "1.2.3"

    resp = app.get("/users/")
    assert resp.status_int == 200
    assert resp.json == [{"display_name": "Damien Accorsi", "id": 1}]

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
    # assert resp.status_int == 400
    # FIXME - G.M - 2019-05-13 - Broken in serpyco: see https://gitlab.com/sgrignard/serpyco/issues/28,
    # assert json_ == {
    #     "message": 'Validation error of input data: "data: is missing required properties "first_name", "email_address", "display_name"."',
    #     "details": {
    #         "#": 'data: is missing required properties "first_name", "email_address", "display_name"."'
    #     },
    #     "code": None,
    # }

    user = {
        "email_address": "some.user@hapic.com",
        "last_name": "Accorsi",
        "first_name": "Damien",
        "company": "Algoo",
    }
    resp = app.post_json("/users/", user, status="*")
    # FIXME - G.M - 2019-05-13 - Broken in serpyco: see https://gitlab.com/sgrignard/serpyco/issues/27
    # assert resp.status_int == 200
    # assert resp.json == {
    #     "last_name": "Accorsi",
    #     "first_name": "Damien",
    #     "id": 2,
    #     "email_address": "some.user@hapic.com",
    #     "company": "Algoo",
    #     "display_name": "Damien Accorsi",
    # }

    resp = app.delete("/users/1", status="*")
    assert resp.status_int == 204


async def test_func__test_usermanagment_endpoints_ok__aiohttp(aiohttp_client, loop):
    UserLib.reset_database()
    context = get_aiohttp_context(loop)
    app = context["app"]
    client = await aiohttp_client(app)
    resp = await client.get("/about")
    json_ = await resp.json()
    assert resp.status == 200
    assert json_["datetime"]
    assert json_["version"] == "1.2.3"

    resp = await client.get("/users/")
    json_ = await resp.json()
    assert resp.status == 200
    assert json_ == [{"display_name": "Damien Accorsi", "id": 1}]

    resp = await client.get("/users/1")
    json_ = await resp.json()
    assert resp.status == 200
    assert json_ == {
        "last_name": "Accorsi",
        "first_name": "Damien",
        "id": 1,
        "display_name": "Damien Accorsi",
        "email_address": "damien.accorsi@algoo.fr",
        "company": "Algoo",
    }

    resp = await client.post("/users/")
    json_ = await resp.json()
    assert resp.status == 400
    # FIXME - G.M - 2019-05-13 - Broken in serpyco: see https://gitlab.com/sgrignard/serpyco/issues/28,
    # assert json_ == {
    #     "message": 'Validation error of input data: "data: is missing required properties "first_name", "email_address", "display_name"."',
    #     "details": {
    #         "#": 'data: is missing required properties "first_name", "email_address", "display_name"."'
    #     },
    #     "code": None,
    # }

    user = {
        "email_address": "some.user@hapic.com",
        "last_name": "Accorsi",
        "first_name": "Damien",
        "company": "Algoo",
    }

    resp = await client.post("/users/", data=user)
    json_ = await resp.json()
    # FIXME - G.M - 2019-05-13 - Broken in serpyco: see https://gitlab.com/sgrignard/serpyco/issues/27
    # assert resp.status_int == 200
    # assert resp.json == {
    #     "last_name": "Accorsi",
    #     "first_name": "Damien",
    #     "id": 2,
    #     "email_address": "some.user@hapic.com",
    #     "company": "Algoo",
    #     "display_name": "Damien Accorsi",
    # }

    resp = await client.delete("/users/1")
    assert resp.status == 204


def check_serpyco_doc(doc):
    assert doc["info"] == {
        "description": "just an example of hapic API",
        "title": "Fake API",
        "version": "1.0.0",
    }
    assert doc["swagger"] == "2.0"
    assert doc["paths"]["/about"] == {
        "get": {
            "responses": {
                "200": {"description": "200", "schema": {"$ref": "#/definitions/AboutSchema"}}
            },
            "description": "This endpoint allow to check that the API is running. This description\n        is generated from the docstring of the method.",
        }
    }
    assert doc["paths"]["/users/"] == {
        "get": {
            "responses": {
                "200": {"description": "200", "schema": {"$ref": "#/definitions/UserDigestSchema"}}
            },
            "description": "Obtain users list.",
        },
        "post": {
            "parameters": [
                {
                    "in": "body",
                    "name": "body",
                    "schema": {"$ref": "#/definitions/UserSchema_exclude_id"},
                }
            ],
            "responses": {
                "200": {"description": "200", "schema": {"$ref": "#/definitions/UserSchema"}}
            },
            "description": "Add a user to the list",
        },
    }
    assert doc["paths"]["/users/{id}"] == {
        "get": {
            "responses": {
                "200": {"description": "200", "schema": {"$ref": "#/definitions/UserSchema"}},
                "404": {
                    "description": "NOT_FOUND: Nothing matches the given URI",
                    "schema": {"$ref": "#/definitions/DefaultErrorSchema"},
                },
            },
            "parameters": [
                {"type": "integer", "minimum": 1, "in": "path", "name": "id", "required": True}
            ],
            "description": "Return a user taken from the list or return a 404",
        },
        "delete": {
            "responses": {
                "204": {"description": "204", "schema": {"$ref": "#/definitions/NoContentSchema"}},
                "404": {
                    "description": "NOT_FOUND: Nothing matches the given URI",
                    "schema": {"$ref": "#/definitions/DefaultErrorSchema"},
                },
            },
            "parameters": [
                {"type": "integer", "minimum": 1, "in": "path", "name": "id", "required": True}
            ],
        },
    }
    assert doc["paths"]["/users/{id}/avatar"] == {
        "get": {
            "produces": ["image/png"],
            "responses": {
                "200": {"description": "200"},
                "404": {
                    "description": "NOT_FOUND: Nothing matches the given URI",
                    "schema": {"$ref": "#/definitions/DefaultErrorSchema"},
                },
            },
            "parameters": [
                {"type": "integer", "minimum": 1, "in": "path", "name": "id", "required": True}
            ],
        },
        "put": {
            "responses": {
                "204": {"description": "204", "schema": {"$ref": "#/definitions/NoContentSchema"}},
                "400": {
                    "description": "BAD_REQUEST: Bad request syntax or unsupported method",
                    "schema": {"$ref": "#/definitions/DefaultErrorSchema"},
                },
                "404": {
                    "description": "NOT_FOUND: Nothing matches the given URI",
                    "schema": {"$ref": "#/definitions/DefaultErrorSchema"},
                },
            },
            "parameters": [
                {"type": "integer", "minimum": 1, "in": "path", "name": "id", "required": True},
                {"type": "file", "in": "formData", "name": "avatar", "required": True},
            ],
            "consumes": ["multipart/form-data"],
        },
    }

    assert doc["definitions"]["AboutSchema"] == {
        "type": "object",
        "properties": {
            "version": {"type": "string"},
            "datetime": {
                "type": "string",
                "format": "date-time",
                "pattern": "^[0-9]{4}-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9](\\.[0-9]+)?(([+-][0-9][0-9]:[0-9][0-9])|Z)?$",
            },
        },
        "required": ["datetime", "version"],
        "description": "Representation of the /about route",
    }
    assert doc["definitions"]["UserSchema"] == {
        "type": "object",
        "properties": {
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
            "display_name": {"type": "string"},
            "company": {"type": "string"},
            "id": {"type": "integer"},
            "email_address": {"type": "string", "format": "email"},
        },
        "required": ["display_name", "email_address", "first_name", "id"],
        "description": "Complete representation of a user",
    }
    assert doc["definitions"]["NoContentSchema"] == {
        "type": "object",
        "properties": {},
        "description": "A docstring to prevent auto generated docstring",
    }
    assert doc["definitions"]["DefaultErrorSchema"] == {
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "details": {"type": "object", "additionalProperties": {}, "default": {}},
            "code": {"default": None},
        },
        "required": ["code", "details", "message"],
        "description": "DefaultErrorSchema(message:str, details:Dict[str, Any]=<factory>, code:Any=None)",
    }
    assert doc["definitions"]["UserSchema_exclude_id"] == {
        "type": "object",
        "properties": {
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
            "display_name": {"type": "string"},
            "company": {"type": "string"},
            "email_address": {"type": "string", "format": "email"},
        },
        "required": ["display_name", "email_address", "first_name"],
        "description": "Complete representation of a user",
    }
    assert doc["definitions"]["UserIdPathSchema"] == {
        "type": "object",
        "properties": {"id": {"type": "integer", "minimum": 1}},
        "required": ["id"],
        "description": "representation of a user id in the uri. This allow to define rules for\n    what is expected. For example, you may want to limit id to number between\n    1 and 999",
    }
    assert doc["definitions"]["UserDigestSchema"] == {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "display_name": {"type": "string", "default": ""},
        },
        "required": ["display_name", "id"],
        "description": "User representation for listing",
    }


@pytest.mark.parametrize(
    "context", [get_bottle_context(), get_flask_context(), get_pyramid_context()]
)
def test_func__test_usermanagment_doc_ok__sync_frameworks(context):
    UserLib.reset_database()
    hapic = context["hapic"]
    doc = hapic.generate_doc(title="Fake API", description="just an example of hapic API")
    # INFO BS 2019-04-15: Prevent keep of OrderedDict
    doc = json.loads(json.dumps(doc))
    check_serpyco_doc(doc)


async def test_func_test__usermanagment_doc_ok_aiohttp(loop):
    UserLib.reset_database()
    context = get_aiohttp_context(loop)
    hapic = context["hapic"]
    doc = hapic.generate_doc(title="Fake API", description="just an example of hapic API")
    doc = json.loads(json.dumps(doc))
    check_serpyco_doc(doc)
