# coding: utf-8
import marshmallow
import bottle
from marshmallow.validate import OneOf

from hapic import Hapic
from tests.base import Base
from tests.base import MyContext


class TestDocGeneration(Base):
    def test_func__input_files_doc__ok__one_file(self):
        hapic = Hapic()
        # TODO BS 20171113: Make this test non-bottle
        app = bottle.Bottle()
        hapic.set_context(MyContext(app=app))

        class MySchema(marshmallow.Schema):
            file_abc = marshmallow.fields.Raw(required=True)

        @hapic.with_api_doc()
        @hapic.input_files(MySchema())
        def my_controller(hapic_data=None):
            assert hapic_data
            assert hapic_data.files

        app.route('/upload', method='POST', callback=my_controller)
        doc = hapic.generate_doc()

        assert doc
        assert '/upload' in doc['paths']
        assert 'consumes' in doc['paths']['/upload']['post']
        assert 'multipart/form-data' in doc['paths']['/upload']['post']['consumes']  # nopep8
        assert 'parameters' in doc['paths']['/upload']['post']
        assert {
                   'name': 'file_abc',
                   'required': True,
                   'in': 'formData',
                   'type': 'file',
               } in doc['paths']['/upload']['post']['parameters']

    def test_func__input_files_doc__ok__two_file(self):
        hapic = Hapic()
        # TODO BS 20171113: Make this test non-bottle
        app = bottle.Bottle()
        hapic.set_context(MyContext(app=app))

        class MySchema(marshmallow.Schema):
            file_abc = marshmallow.fields.Raw(required=True)
            file_def = marshmallow.fields.Raw(required=False)

        @hapic.with_api_doc()
        @hapic.input_files(MySchema())
        def my_controller(hapic_data=None):
            assert hapic_data
            assert hapic_data.files

        app.route('/upload', method='POST', callback=my_controller)
        doc = hapic.generate_doc()

        assert doc
        assert '/upload' in doc['paths']
        assert 'consumes' in doc['paths']['/upload']['post']
        assert 'multipart/form-data' in doc['paths']['/upload']['post']['consumes']  # nopep8
        assert 'parameters' in doc['paths']['/upload']['post']
        assert {
                   'name': 'file_abc',
                   'required': True,
                   'in': 'formData',
                   'type': 'file',
               } in doc['paths']['/upload']['post']['parameters']
        assert {
                   'name': 'file_def',
                   'required': False,
                   'in': 'formData',
                   'type': 'file',
               } in doc['paths']['/upload']['post']['parameters']

    def test_func__output_file_doc__ok__nominal_case(self):
        hapic = Hapic()
        # TODO BS 20171113: Make this test non-bottle
        app = bottle.Bottle()
        hapic.set_context(MyContext(app=app))

        @hapic.with_api_doc()
        @hapic.output_file(['image/jpeg'])
        def my_controller():
            return b'101010100101'

        app.route('/avatar', method='GET', callback=my_controller)
        doc = hapic.generate_doc()

        assert doc
        assert '/avatar' in doc['paths']
        assert 'produces' in doc['paths']['/avatar']['get']
        assert 'image/jpeg' in doc['paths']['/avatar']['get']['produces']
        assert 200 in doc['paths']['/avatar']['get']['responses']

    def test_func__input_files_doc__ok__one_file_and_text(self):
        hapic = Hapic()
        # TODO BS 20171113: Make this test non-bottle
        app = bottle.Bottle()
        hapic.set_context(MyContext(app=app))

        class MySchema(marshmallow.Schema):
            name = marshmallow.fields.String(required=True)

        class MyFilesSchema(marshmallow.Schema):
            file_abc = marshmallow.fields.Raw(required=True)

        @hapic.with_api_doc()
        @hapic.input_files(MyFilesSchema())
        @hapic.input_body(MySchema())
        def my_controller(hapic_data=None):
            assert hapic_data
            assert hapic_data.files

        app.route('/upload', method='POST', callback=my_controller)
        doc = hapic.generate_doc()

        assert doc
        assert '/upload' in doc['paths']
        assert 'consumes' in doc['paths']['/upload']['post']
        assert 'multipart/form-data' in doc['paths']['/upload']['post']['consumes']  # nopep8
        assert 'parameters' in doc['paths']['/upload']['post']
        assert {
                   'name': 'file_abc',
                   'required': True,
                   'in': 'formData',
                   'type': 'file',
               } in doc['paths']['/upload']['post']['parameters']

    def test_func__docstring__ok__simple_case(self):
        hapic = Hapic()
        app = bottle.Bottle()
        hapic.set_context(MyContext(app=app))

        # TODO BS 20171113: Make this test non-bottle
        @hapic.with_api_doc()
        def my_controller(hapic_data=None):
            """
            Hello doc
            """
            assert hapic_data
            assert hapic_data.files

        app.route('/upload', method='POST', callback=my_controller)
        doc = hapic.generate_doc()

        assert doc.get('paths')
        assert '/upload' in doc['paths']
        assert 'post' in doc['paths']['/upload']
        assert 'description' in doc['paths']['/upload']['post']
        assert 'Hello doc' == doc['paths']['/upload']['post']['description']

    def test_func__tags__ok__nominal_case(self):
        hapic = Hapic()
        app = bottle.Bottle()
        hapic.set_context(MyContext(app=app))

        @hapic.with_api_doc(tags=['foo', 'bar'])
        def my_controller(hapic_data=None):
            assert hapic_data
            assert hapic_data.files

        app.route('/upload', method='POST', callback=my_controller)
        doc = hapic.generate_doc()

        assert doc.get('paths')
        assert '/upload' in doc['paths']
        assert 'post' in doc['paths']['/upload']
        assert 'tags' in doc['paths']['/upload']['post']
        assert ['foo', 'bar'] == doc['paths']['/upload']['post']['tags']

    def test_func__errors__nominal_case(self):
        hapic = Hapic()
        app = bottle.Bottle()
        hapic.set_context(MyContext(app=app))

        @hapic.with_api_doc()
        @hapic.handle_exception()
        def my_controller(hapic_data=None):
            assert hapic_data

        app.route('/upload', method='POST', callback=my_controller)
        doc = hapic.generate_doc()

        assert doc.get('paths')
        assert '/upload' in doc['paths']
        assert 'post' in doc['paths']['/upload']
        assert 'responses' in doc['paths']['/upload']['post']
        assert 500 in doc['paths']['/upload']['post']['responses']
        assert {
            'description': "500",
            'schema': {
                '$ref': '#/definitions/DefaultErrorBuilder'
            }
        } == doc['paths']['/upload']['post']['responses'][500]

    def test_func__enum__nominal_case(self):
        hapic = Hapic()
        # TODO BS 20171113: Make this test non-bottle
        app = bottle.Bottle()
        hapic.set_context(MyContext(app=app))

        class MySchema(marshmallow.Schema):
            category = marshmallow.fields.String(
                validate=OneOf(['foo', 'bar'])
            )

        @hapic.with_api_doc()
        @hapic.input_body(MySchema())
        def my_controller():
            return

        app.route('/paper', method='POST', callback=my_controller)
        doc = hapic.generate_doc()

        assert ['foo', 'bar'] == doc.get('definitions', {})\
            .get('MySchema', {})\
            .get('properties', {})\
            .get('category', {})\
            .get('enum')

    def test_func__schema_in_doc__ok__nominal_case(self):
        hapic = Hapic()
        app = bottle.Bottle()
        hapic.set_context(MyContext(app=app))

        class MySchema(marshmallow.Schema):
            name = marshmallow.fields.String(required=True)

        @hapic.with_api_doc()
        @hapic.input_body(MySchema())
        def my_controller():
            return {'name': 'test',}

        app.route('/paper', method='POST', callback=my_controller)
        doc = hapic.generate_doc()

        assert doc.get('definitions', {}).get('MySchema', {})
        schema_def = doc.get('definitions', {}).get('MySchema', {})
        assert schema_def.get('properties', {}).get('name', {}).get('type')

        assert doc.get('paths').get('/paper').get('post').get('parameters')[0]
        schema_ref = doc.get('paths').get('/paper').get('post').get('parameters')[0]
        assert schema_ref.get('in') == 'body'
        assert schema_ref.get('name') == 'body'
        assert schema_ref['schema']['$ref'] == '#/definitions/MySchema'

    def test_func__schema_in_doc__ok__many_case(self):
        hapic = Hapic()
        app = bottle.Bottle()
        hapic.set_context(MyContext(app=app))

        class MySchema(marshmallow.Schema):
            name = marshmallow.fields.String(required=True)

        @hapic.with_api_doc()
        @hapic.input_body(MySchema(many=True))
        def my_controller():
            return {'name': 'test'}

        app.route('/paper', method='POST', callback=my_controller)
        doc = hapic.generate_doc()

        assert doc.get('definitions', {}).get('MySchema', {})
        schema_def = doc.get('definitions', {}).get('MySchema', {})
        assert schema_def.get('properties', {}).get('name', {}).get('type')

        assert doc.get('paths').get('/paper').get('post').get('parameters')[0]
        schema_ref = doc.get('paths').get('/paper').get('post').get('parameters')[0]
        assert schema_ref.get('in') == 'body'
        assert schema_ref.get('name') == 'body'
        assert schema_ref['schema'] == {
            'items': {'$ref': '#/definitions/MySchema'},
            'type': 'array'
        }

    def test_func__schema_in_doc__ok__exclude_case(self):
        hapic = Hapic()
        app = bottle.Bottle()
        hapic.set_context(MyContext(app=app))

        class MySchema(marshmallow.Schema):
            name = marshmallow.fields.String(required=True)
            name2 = marshmallow.fields.String(required=True)

        @hapic.with_api_doc()
        @hapic.input_body(MySchema(exclude=('name2',)))
        def my_controller():
            return {'name': 'test',}

        app.route('/paper', method='POST', callback=my_controller)
        doc = hapic.generate_doc()

        definitions = doc.get('definitions', {})
        # TODO - G-M - Find better way to find our new schema
        # Do Better test when we were able to set correctly schema name
        # according to content
        schema_name = None
        for elem in definitions.keys():
            if elem != 'MySchema':
                schema_name = elem
                break
        assert schema_name
        schema_def = definitions[schema_name]
        assert schema_def.get('properties', {}).get('name', {}).get('type') == 'string'
        assert doc.get('paths').get('/paper').get('post').get('parameters')[0]
        schema_ref = doc.get('paths').get('/paper').get('post').get('parameters')[0]
        assert schema_ref.get('in') == 'body'
        assert schema_ref['schema']['$ref'] == '#/definitions/{}'.format(schema_name)

        @hapic.with_api_doc()
        @hapic.input_body(MySchema(only=('name',)))
        def my_controller():
            return {'name': 'test'}

        app.route('/paper', method='POST', callback=my_controller)
        doc = hapic.generate_doc()

        # TODO - G-M - Find better way to find our new schema
        # Do Better test when we were able to set correctly schema name
        # according to content
        definitions = doc.get('definitions', {})
        schema_name = None
        for elem in definitions.keys():
            if elem != 'MySchema':
                schema_name = elem
                break
        assert schema_name
        schema_def = definitions[schema_name]
        assert schema_def.get('properties', {}).get('name', {}).get('type') == 'string'
        assert doc.get('paths').get('/paper').get('post').get('parameters')[0]
        schema_ref = doc.get('paths').get('/paper').get('post').get('parameters')[0]
        assert schema_ref.get('in') == 'body'
        assert schema_ref['schema']['$ref'] == '#/definitions/{}'.format(schema_name)

    def test_func__schema_in_doc__ok__many_and_exclude_case(self):
        hapic = Hapic()
        app = bottle.Bottle()
        hapic.set_context(MyContext(app=app))

        class MySchema(marshmallow.Schema):
            name = marshmallow.fields.String(required=True)
            name2 = marshmallow.fields.String(required=True)

        @hapic.with_api_doc()
        @hapic.input_body(MySchema(exclude=('name2',), many=True))
        def my_controller():
            return {'name': 'test',}

        app.route('/paper', method='POST', callback=my_controller)
        doc = hapic.generate_doc()

        definitions = doc.get('definitions', {})
        # TODO - G-M - Find better way to find our new schema
        # Do Better test when we were able to set correctly schema name
        # according to content
        schema_name = None
        for elem in definitions.keys():
            if elem != 'MySchema':
                schema_name = elem
                break
        assert schema_name
        schema_def = definitions[schema_name]
        assert schema_def.get('properties', {}).get('name', {}).get('type') == 'string'
        assert doc.get('paths').get('/paper').get('post').get('parameters')[0]
        schema_ref = doc.get('paths').get('/paper').get('post').get('parameters')[0]
        assert schema_ref.get('in') == 'body'
        assert schema_ref['schema'] == {
            'items': {'$ref': '#/definitions/{}'.format(schema_name)},
            'type': 'array'
        }
