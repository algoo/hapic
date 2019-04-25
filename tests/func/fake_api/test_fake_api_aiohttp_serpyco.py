# coding: utf-8
from aiohttp import web
import pytest

from example.fake_api.aiohttp_serpyco import AiohttpSerpycoController
from hapic.error.serpyco import SerpycoDefaultErrorBuilder
from hapic.ext.aiohttp.context import AiohttpContext
from tests.func.fake_api.common_serpyco import serpyco_SWAGGER_DOC_API


def create_aiohttp_serpyco_app(loop):
    controller = AiohttpSerpycoController()
    app = web.Application(loop=loop)
    controller.bind(app)
    return app


def get_aiohttp_serpyco_app_hapic(app):
    from example.fake_api.aiohttp_serpyco import hapic

    hapic.reset_context()
    hapic.set_context(AiohttpContext(app, default_error_builder=SerpycoDefaultErrorBuilder()))
    return hapic


async def test_func__test_fake_api_endpoints_ok__aiohttp(test_client,):
    app = await test_client(create_aiohttp_serpyco_app)
    get_aiohttp_serpyco_app_hapic(app)
    resp = await app.get("/about")
    assert resp.status == 200
    json_ = await resp.json()
    assert json_ == {"datetime": "2017-12-07T10:55:08.488996+00:00", "version": "1.2.3"}

    resp = await app.get("/users")
    assert resp.status == 200
    json_ = await resp.json()
    assert json_ == {
        "items": [
            {"username": "some_user", "display_name": "Damien Accorsi", "company": "Algoo", "id": 4}
        ],
        "pagination": {"first_id": 0, "last_id": 5, "current_id": 0},
        "item_nb": 1,
    }

    resp = await app.get("/users2")
    assert resp.status == 200
    json_ = await resp.json()
    assert json_ == [
        {"username": "some_user", "id": 4, "display_name": "Damien Accorsi", "company": "Algoo"}
    ]

    resp = await app.get("/users/1")
    assert resp.status == 200
    json_ = await resp.json()
    assert json_ == {
        "last_name": "Accorsi",
        "username": "some_user",
        "first_name": "Damien",
        "id": 4,
        "display_name": "Damien Accorsi",
        "email_address": "some.user@hapic.com",
        "company": "Algoo",
    }

    resp = await app.get("/users/abc")  # int expected
    assert resp.status == 400
    json_ = await resp.json()
    assert (
        'Validation error of input data: "Could not cast field id: invalid '
        "literal for int() with base 10: 'abc'\"" == json_.get("message")
    )

    resp = await app.post("/users/")
    assert resp.status == 400
    json_ = await resp.json()

    assert 'Validation error of input data: "data: is missing required properties' in json_.get(
        "message"
    )

    assert "email_address" in json_.get("message")
    assert "last_name" in json_.get("message")
    assert "display_name" in json_.get("message")
    assert "company" in json_.get("message")
    assert "username" in json_.get("message")
    assert "first_name" in json_.get("message")

    user = {
        "email_address": "some.user@hapic.com",
        "username": "some_user",
        "display_name": "Damien Accorsi",
        "last_name": "Accorsi",
        "first_name": "Damien",
        "company": "Algoo",
    }

    resp = await app.post("/users/", data=user)
    assert resp.status == 200
    json_ = await resp.json()
    assert json_ == {
        "last_name": "Accorsi",
        "username": "some_user",
        "first_name": "Damien",
        "id": 4,
        "display_name": "Damien Accorsi",
        "email_address": "some.user@hapic.com",
        "company": "Algoo",
    }

    resp = await app.delete("/users/1")
    assert resp.status == 204


@pytest.mark.xfail(
    reason="unconsistent test. " "see issue #147(https://github.com/algoo/hapic/issues/147)"
)
async def test_func__test_fake_api_doc_ok__aiohttp_serpyco(test_client):
    app = web.Application()
    controllers = AiohttpSerpycoController()
    controllers.bind(app)
    hapic = get_aiohttp_serpyco_app_hapic(app)
    doc = hapic.generate_doc(title="Fake API", description="just an example of hapic API")
    # FIXME BS 2018-11-26: Test produced doc atomic
    assert serpyco_SWAGGER_DOC_API == doc
