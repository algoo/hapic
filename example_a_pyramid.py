# -*- coding: utf-8 -*-
import json
from http import HTTPStatus

#import bottle
from pyramid.config import Configurator
from wsgiref.simple_server import make_server
import time
import yaml
import uuid
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


class Controllers(object):
    @hapic.with_api_doc()
    # @hapic.ext.bottle.bottle_context()
    @hapic.handle_exception(ZeroDivisionError, http_code=HTTPStatus.BAD_REQUEST)
    @hapic.input_path(HelloPathSchema())
    @hapic.input_query(HelloQuerySchema())
    @hapic.output_body(HelloResponseSchema())
    def hello(self, context, request, hapic_data: HapicData):
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
        name = request.matchdict.get('name', None)
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
    def hello2(self, context, request, hapic_data: HapicData):
        name = request.matchdict.get('name', None)
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
    def hello3(self, context, request, hapic_data: HapicData):
        name = request.matchdict.get('name', None)
        return {
            'sentence': 'Hello !',
            'name': name,
        }

    def bind(self, app):
        app.route('/hello/{name}', callback=self.hello)
        app.route('/hello/{name}', callback=self.hello2, method='POST')
        app.route('/hello3/{name}', callback=self.hello3)
        app.config.include('pyramid_debugtoolbar')


class PyramRoute(object):

    def __init__(self, app, rule, method, callback, name, **options):
        self.app = app
        self.rule = rule
        self.method = method
        self.callback = callback
        self.name = name

        if not self.name:
            self.name = str(uuid.uuid4())

        with self.app.config as config:
            config.add_route(self.name, self.rule, request_method=self.method)
            config.add_view(
                self.callback, route_name=self.name, renderer='json')
        #import pdb; pdb.set_trace()


class Pyramidapp(object):

    def __init__(self):
        self.config = Configurator()
        self.routes = []

    def route(self,
              rule,
              callback,
              method='GET',
              name=None,
              **options):
        r = PyramRoute(self, rule, method, callback, name, **options)
        self.routes.append(r)

    def run(self, host, port, debug):
        server = make_server('0.0.0.0', port, self.config.make_wsgi_app())
        server.serve_forever()


app = Pyramidapp()

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

# hapic.set_context(hapic.ext.bottle.BottleContext())
hapic.set_context(hapic.ext.pyramid.PyramidContext())
#import pdb; pdb.set_trace()
print(json.dumps(hapic.generate_doc(app)))
app.run('localhost', 8080, True)
#server = make_server('0.0.0.0', 8080, app.config.make_wsgi_app())
# server.serve_forever()
