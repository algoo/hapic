# -*- coding: utf-8 -*-
import json
from http import HTTPStatus

from flask import Flask
import time
import yaml
from beaker.middleware import SessionMiddleware

import hapic
from example import HelloResponseSchema, HelloPathSchema, HelloJsonSchema, \
    ErrorResponseSchema, HelloQuerySchema
from hapic.data import HapicData

# hapic.global_exception_handler(UnAuthExc, StandardErrorSchema)
# hapic.global_exception_handler(UnAuthExc2, StandardErrorSchema)
# hapic.global_exception_handler(UnAuthExc3, StandardErrorSchema)
# bottle.default_app.push(app)

# session_opts = {
#     'session.type': 'file',
#     'session.data_dir': '/tmp',
#     'session.cookie_expires': 3600,
#     'session.auto': True
# }
# session_middleware = SessionMiddleware(
#     app,
#     session_opts,
#     environ_key='beaker.session',
#     key='beaker.session.id',
# )
# app = session_middleware.wrap_app


def bob(f):
    def boby(*args, **kwargs):
        return f(*args, **kwargs)
    return boby


class FlaskRoute(object):

    def __init__(self, app, rule, method, callback, name, **options):
        self.app = app
        self.rule = rule
        self.method = method
        self.callback = callback
        self.name = name


class Flaskapp(Flask):
    @property
    def routes(self):
        result = []
        for r in self.url_map.iter_rules():
            rule = r.rule
            callback = self.view_functions[r.endpoint]
            method = [x for x in r.methods if x not in [
                'OPTIONS', 'HEAD']][0]  # TODO : other solution ?
            name = r.endpoint
            app = self
            f = FlaskRoute(self, rule, method, callback, name)
            result.append(f)
        return result


app = Flaskapp(__name__)


class Controllers(object):
    @hapic.with_api_doc()
    # @hapic.ext.bottle.bottle_context()
    @hapic.handle_exception(ZeroDivisionError, http_code=HTTPStatus.BAD_REQUEST)
    @hapic.input_path(HelloPathSchema())
    @hapic.input_query(HelloQuerySchema())
    @hapic.output_body(HelloResponseSchema())
    def hello(self, name: str, hapic_data: HapicData):
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
    def hello2(self, name: str, hapic_data: HapicData):
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
    def hello3(self, name: str,hapic_data: HapicData ):
        return {
            'sentence': 'Hello !',
            'name': name,
        }

    def bind(self, app):
        pass
        app.add_url_rule('/hello/<name>', "hello", self.hello)
        app.add_url_rule('/hello/<name>', "hello2",
                         self.hello2, methods=['POST', ])
        app.add_url_rule('/hello3/<name>', "hello3", self.hello3)

#app = bottle.Bottle()


controllers = Controllers()
controllers.bind(app)


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

hapic.set_context(hapic.ext.flask.FlaskContext(app))
print(json.dumps(hapic.generate_doc()))
#import pdb; pdb.set_trace()
app.run(host='localhost', port=8080, debug=True)
