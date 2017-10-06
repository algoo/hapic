# -*- coding: utf-8 -*-
import json
from http import HTTPStatus

import bottle
import time
import yaml

import hapic
from example import HelloResponseSchema, HelloPathSchema, HelloJsonSchema, \
    ErrorResponseSchema, HelloQuerySchema
from hapic.data import HapicData

app = bottle.Bottle()


def bob(f):
    def boby(*args, **kwargs):
        return f(*args, **kwargs)
    return boby


@hapic.with_api_doc()
# @hapic.ext.bottle.bottle_context()
@hapic.handle_exception(ZeroDivisionError, http_code=HTTPStatus.BAD_REQUEST)
@hapic.input_path(HelloPathSchema())
@hapic.input_query(HelloQuerySchema())
@hapic.output_body(HelloResponseSchema())
def hello(name: str, hapic_data: HapicData):
    """
    my endpoint hello
    ---
    get:
        description: my description
        parameters:
            - in: "path"
              description: "hello"
              name: "name"
              type: "string"
        responses:
            200:
                description: A pet to be returned
                schema: HelloResponseSchema
    """
    if name == 'zero':
        raise ZeroDivisionError('Don\'t call him zero !')

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
@hapic.input_path(HelloPathSchema())
@hapic.output_body(HelloResponseSchema())
def hello3(name: str):
    return {
        'sentence': 'Hello !',
        'name': name,
    }


app.route('/hello/<name>', callback=hello)
app.route('/hello/<name>', callback=hello2, method='POST')
app.route('/hello3/<name>', callback=hello3)

# time.sleep(1)
# s = hapic.generate_doc(app)
# ss = json.loads(json.dumps(s))
# for path in ss['paths']:
#     for method in ss['paths'][path]:
#         for response_code in ss['paths'][path][method]['responses']:
#             ss['paths'][path][method]['responses'][int(response_code)] = ss['paths'][path][method]['responses'][response_code]
#             del ss['paths'][path][method]['responses'][int(response_code)]
# print(yaml.dump(ss, default_flow_style=False))
# time.sleep(1)

print(json.dumps(hapic.generate_doc(app)))

app.run(host='localhost', port=8080, debug=True)
