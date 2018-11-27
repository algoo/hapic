import copy

from aiohttp import web
from bottle import Bottle
from flask import Flask
from pyramid.config import Configurator
import pytest
from webtest import TestApp

from example.fake_api.aiohttp_serpyco import AiohttpSerpycoController
from example.fake_api.bottle_api import BottleController
from example.fake_api.flask_api import FlaskController
from example.fake_api.pyramid_api import PyramidController
from hapic.ext.aiohttp.context import AiohttpContext
from hapic.ext.bottle import BottleContext
from hapic.ext.flask import FlaskContext
from hapic.ext.pyramid import PyramidContext
from tests.func.fake_api.common import SWAGGER_DOC_API
from tests.func.fake_api.common import serpyco_SWAGGER_DOC_API


def get_bottle_context():
    from example.fake_api.bottle_api import hapic as h
    bottle_app = Bottle()
    h.reset_context()
    h.set_context(BottleContext(bottle_app))
    controllers = BottleController()
    controllers.bind(bottle_app)
    return {
        'hapic': h,
        'app': bottle_app,
    }


def get_flask_context():
    from example.fake_api.flask_api import hapic as h
    flask_app = Flask(__name__)
    controllers = FlaskController()
    controllers.bind(flask_app)
    h.reset_context()
    h.set_context(FlaskContext(flask_app))
    return {
        'hapic': h,
        'app': flask_app,
    }


def get_pyramid_context():
    from example.fake_api.pyramid_api import hapic as h
    configurator = Configurator(autocommit=True)
    controllers = PyramidController()
    controllers.bind(configurator)
    h.reset_context()
    h.set_context(PyramidContext(configurator))
    pyramid_app = configurator.make_wsgi_app()
    return {
        'hapic': h,
        'app': pyramid_app,
    }


def create_aiohttp_serpyco_app(loop):
    controller = AiohttpSerpycoController()
    app = web.Application(loop=loop)
    controller.bind(app)
    return app


def get_aiohttp_serpyco_app_hapic(app):
    from example.fake_api.aiohttp_serpyco import hapic
    hapic.reset_context()
    hapic.set_context(AiohttpContext(app))
    return hapic


@pytest.mark.parametrize('context',
                         [
                             get_bottle_context(),
                             get_flask_context(),
                             get_pyramid_context(),
                         ])
def test_func__test_fake_api_endpoints_ok__all_framework(context):
    hapic = context['hapic']
    app = context['app']
    app = TestApp(app)
    resp = app.get('/about')
    assert resp.status_int == 200
    assert resp.json == {'datetime': '2017-12-07T10:55:08.488996+00:00',
                         'version': '1.2.3'}

    resp = app.get('/users')
    assert resp.status_int == 200
    assert resp.json == {
        'items':
        [
            {
                'username': 'some_user',
                'display_name': 'Damien Accorsi',
                'company': 'Algoo', 'id': 4
            }
        ],
        'pagination': {
            'first_id': 0,
            'last_id': 5,
            'current_id': 0,
        },
        'item_nb': 1,
    }

    resp = app.get('/users2')
    assert resp.status_int == 200
    assert resp.json == [
        {
           'username': 'some_user',
           'id': 4,
           'display_name': 'Damien Accorsi',
           'company': 'Algoo'
        }
    ]

    resp = app.get('/users/1')
    assert resp.status_int == 200
    assert resp.json == {
        'last_name': 'Accorsi',
        'username': 'some_user',
        'first_name': 'Damien',
        'id': 4,
        'display_name': 'Damien Accorsi',
        'email_address': 'some.user@hapic.com',
        'company': 'Algoo'
    }

    resp = app.post('/users/', status='*')
    assert resp.status_int == 400
    assert resp.json == {
        'code': None,
        'details': {
            'email_address': ['Missing data for required field.'],
            'username': ['Missing data for required field.'],
            'display_name': ['Missing data for required field.'],
            'last_name': ['Missing data for required field.'],
            'first_name': ['Missing data for required field.'],
            'company': ['Missing data for required field.']},
        'message': 'Validation error of input data'}

    user = {
        'email_address': 'some.user@hapic.com',
        'username': 'some_user',
        'display_name': 'Damien Accorsi',
        'last_name': 'Accorsi',
        'first_name': 'Damien',
        'company': 'Algoo',
    }

    resp = app.post_json('/users/', user)
    assert resp.status_int == 200
    assert resp.json == {
        'last_name': 'Accorsi',
        'username': 'some_user',
        'first_name': 'Damien',
        'id': 4,
        'display_name': 'Damien Accorsi',
        'email_address': 'some.user@hapic.com',
        'company': 'Algoo',
    }

    resp = app.delete('/users/1', status='*')
    assert resp.status_int == 204


async def test_func__test_fake_api_endpoints_ok__aiohttp(
    test_client,
):
    app = await test_client(create_aiohttp_serpyco_app)
    get_aiohttp_serpyco_app_hapic(app)
    resp = await app.get('/about')
    assert resp.status == 200
    json_ = await resp.json()
    assert json_ == {'datetime': '2017-12-07T10:55:08.488996+00:00',
                         'version': '1.2.3'}

    resp = await app.get('/users')
    assert resp.status == 200
    json_ = await resp.json()
    assert json_ == {
        'items':
        [
            {
                'username': 'some_user',
                'display_name': 'Damien Accorsi',
                'company': 'Algoo', 'id': 4
            }
        ],
        'pagination': {
            'first_id': 0,
            'last_id': 5,
            'current_id': 0,
        },
        'item_nb': 1,
    }

    resp = await app.get('/users2')
    assert resp.status == 200
    json_ = await resp.json()
    assert json_ == [
        {
           'username': 'some_user',
           'id': 4,
           'display_name': 'Damien Accorsi',
           'company': 'Algoo'
        }
    ]

    resp = await app.get('/users/1')
    assert resp.status == 200
    json_ = await resp.json()
    assert json_ == {
        'last_name': 'Accorsi',
        'username': 'some_user',
        'first_name': 'Damien',
        'id': 4,
        'display_name': 'Damien Accorsi',
        'email_address': 'some.user@hapic.com',
        'company': 'Algoo'
    }

    resp = await app.post('/users/')
    assert resp.status == 400
    json_ = await resp.json()

    assert 'Validation error of input data: "data: is ' \
           'missing required properties' in json_.get('message')

    assert 'email_address' in json_.get('message')
    assert 'last_name' in json_.get('message')
    assert 'display_name' in json_.get('message')
    assert 'company' in json_.get('message')
    assert 'username' in json_.get('message')
    assert 'first_name' in json_.get('message')

    user = {
        'email_address': 'some.user@hapic.com',
        'username': 'some_user',
        'display_name': 'Damien Accorsi',
        'last_name': 'Accorsi',
        'first_name': 'Damien',
        'company': 'Algoo',
    }

    resp = await app.post('/users/', data=user)
    assert resp.status == 200
    json_ = await resp.json()
    assert json_ == {
        'last_name': 'Accorsi',
        'username': 'some_user',
        'first_name': 'Damien',
        'id': 4,
        'display_name': 'Damien Accorsi',
        'email_address': 'some.user@hapic.com',
        'company': 'Algoo',
    }

    resp = await app.delete('/users/1')
    assert resp.status == 204


@pytest.mark.parametrize('context',
                         [
                             get_bottle_context(),
                             get_flask_context(),
                             get_pyramid_context()
                         ])
def test_func__test_fake_api_doc_ok__all_framework(context):
    hapic = context['hapic']
    app = context['app']
    app = TestApp(app)
    doc = hapic.generate_doc(
        title='Fake API',
        description='just an example of hapic API'
    )

    assert doc['info'] == SWAGGER_DOC_API['info']
    assert doc['tags'] == SWAGGER_DOC_API['tags']
    assert doc['swagger'] == SWAGGER_DOC_API['swagger']
    assert doc['parameters'] == SWAGGER_DOC_API['parameters']
    assert doc['paths']['/about'] == SWAGGER_DOC_API['paths']['/about']
    assert doc['paths']['/users'] == SWAGGER_DOC_API['paths']['/users']
    assert doc['paths']['/users/{id}'] == SWAGGER_DOC_API['paths']['/users/{id}']
    assert doc['paths']['/users/'] == SWAGGER_DOC_API['paths']['/users/']
    assert doc['paths']['/users2'] == SWAGGER_DOC_API['paths']['/users2']

    assert doc['definitions']['AboutResponseSchema'] == \
           SWAGGER_DOC_API['definitions']['AboutResponseSchema']
    assert doc['definitions']['ListsUserSchema'] == \
           SWAGGER_DOC_API['definitions']['ListsUserSchema']
    assert doc['definitions']['NoContentSchema'] == \
           SWAGGER_DOC_API['definitions']['NoContentSchema']
    assert doc['definitions']['PaginationSchema'] == \
           SWAGGER_DOC_API['definitions']['PaginationSchema']
    assert doc['definitions']['UserSchema'] == \
           SWAGGER_DOC_API['definitions']['UserSchema']
    assert doc['definitions']['UserSchema'] == \
           SWAGGER_DOC_API['definitions']['UserSchema']

    assert doc['definitions']['UserSchema_without_id'] == \
           SWAGGER_DOC_API['definitions']['UserSchema_without_id']
    assert doc['definitions']['UserSchema_without_email_address_first_name_last_name'] == \
           SWAGGER_DOC_API['definitions']['UserSchema_without_email_address_first_name_last_name']


async def test_func__test_fake_api_doc_ok__aiohttp_serpyco(test_client):
    app = web.Application()
    controllers = AiohttpSerpycoController()
    controllers.bind(app)
    hapic = get_aiohttp_serpyco_app_hapic(app)
    doc = hapic.generate_doc(
        title='Fake API',
        description='just an example of hapic API'
    )

    # FIXME BS 2018-11-26: Test produced doc atomic
    assert serpyco_SWAGGER_DOC_API == doc
