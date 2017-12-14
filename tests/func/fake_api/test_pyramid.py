from webtest import TestApp
from pyramid.config import Configurator
import hapic
from hapic.ext.pyramid import PyramidContext
from example.fake_api.pyramid_api import hapic
from example.fake_api.pyramid_api import PyramidController
from tests.func.fake_api.common import SWAGGER_DOC_API


def test_func_pyramid_fake_api_doc():
    configurator = Configurator(autocommit=True)
    controllers = PyramidController()
    controllers.bind(configurator)
    hapic.set_context(PyramidContext(configurator))
    app = TestApp(configurator.make_wsgi_app())
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

    # INFO - G.M - 2017-12-07 - Test for delete desactivated(Webtest check fail)
    # Webtest check content_type. Up to know pyramid_api return json as
    # content_type with 204 NO CONTENT status code which return an error in
    # WebTest check.
    # resp = app.delete('/users/1', status='*')
    # assert resp.status_int == 204
