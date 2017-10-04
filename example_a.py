# -*- coding: utf-8 -*-
import bottle
import hapic
from example import HelloResponseSchema, HelloPathSchema, HelloJsonSchema, \
    ErrorResponseSchema
from hapic.data import HapicData

app = bottle.Bottle()


def bob(f):
    def boby(*args, **kwargs):
        return f(*args, **kwargs)
    return boby


@hapic.with_api_doc()
# @hapic.ext.bottle.bottle_context()
# @hapic.error_schema(ErrorResponseSchema())
@hapic.input_path(HelloPathSchema())
@hapic.output_body(HelloResponseSchema())
def hello(name: str, hapic_data: HapicData):
    return {
        'sentence': 'Hello !',
        'name': name,
    }


@hapic.with_api_doc()
# @hapic.ext.bottle.bottle_context()
# @hapic.error_schema(ErrorResponseSchema())
@hapic.input_path(HelloPathSchema())
@hapic.input_body(HelloJsonSchema())
@hapic.output_body(HelloResponseSchema())
@bob
def hello2(name: str, hapic_data: HapicData):
    return {
        'sentence': 'Hello !',
        'name': name,
        'color': hapic_data.body.get('color'),
    }

kwargs = {'validated_data': {'name': 'bob'}, 'name': 'bob'}


@hapic.with_api_doc()
# @hapic.ext.bottle.bottle_context()
# @hapic.error_schema(ErrorResponseSchema())
@hapic.output_body(HelloResponseSchema())
def hello3(name: str):
    return {
        'sentence': 'Hello !',
        'name': name,
    }


app.route('/hello/<name>', callback=hello)
app.route('/hello2/<name>', callback=hello2, method='POST')
app.route('/hello3/<name>', callback=hello3)

hapic.generate_doc(app)
app.run(host='localhost', port=8080, debug=True)
