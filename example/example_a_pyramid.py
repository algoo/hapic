# -*- coding: utf-8 -*-
import json
from http import HTTPStatus

from pyramid.config import Configurator
from wsgiref.simple_server import make_server

import hapic
from example import HelloResponseSchema, HelloPathSchema, HelloJsonSchema, \
    ErrorResponseSchema, HelloQuerySchema
from hapic.data import HapicData
from hapic.ext.pyramid import PyramidContext


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

    def bind(self, configurator: Configurator):
        configurator.add_route('hello', '/hello/{name}', request_method='GET')
        configurator.add_view(self.hello, route_name='hello', renderer='json')

        configurator.add_route('hello2', '/hello/{name}', request_method='POST')  # nopep8
        configurator.add_view(self.hello2, route_name='hello2', renderer='json')  # nopep8

        configurator.add_route('hello3', '/hello3/{name}', request_method='GET')  # nopep8
        configurator.add_view(self.hello3, route_name='hello3', renderer='json')  # nopep8


configurator = Configurator(autocommit=True)
controllers = Controllers()

controllers.bind(configurator)

hapic.set_context(PyramidContext(configurator))
print(json.dumps(hapic.generate_doc()))

server = make_server('0.0.0.0', 8080, configurator.make_wsgi_app())
server.serve_forever()
