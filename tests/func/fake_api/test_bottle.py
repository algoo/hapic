from webtest import TestApp
from bottle import Bottle

from hapic.ext.bottle import BottleContext
from example.fake_api.bottle_api import BottleController
from tests.func.fake_api.common import SWAGGER_DOC_API
from example.fake_api.bottle_api import hapic


def test_func_bottle_fake_api():
    bottle_app = Bottle()
    controllers = BottleController()
    controllers.bind(bottle_app)

    hapic.set_context(BottleContext(bottle_app))
    app = TestApp(bottle_app)
    doc = hapic.generate_doc(
        title='Fake API',
        description='just an example of hapic API'
    )

    assert doc == SWAGGER_DOC_API
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

