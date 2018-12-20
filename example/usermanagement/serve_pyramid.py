# -*- coding: utf-8 -*-

from datetime import datetime

from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder

try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus
import json
from pyramid.config import Configurator
import time
from wsgiref.simple_server import make_server

from hapic import Hapic
from hapic.data import HapicData
from hapic.ext.pyramid import PyramidContext

from example.usermanagement.schema import AboutSchema
from example.usermanagement.schema import NoContentSchema
from example.usermanagement.schema import UserDigestSchema
from example.usermanagement.schema import UserIdPathSchema
from example.usermanagement.schema import UserSchema

from example.usermanagement.userlib import User
from example.usermanagement.userlib import UserLib
from example.usermanagement.userlib import UserNotFound

hapic = Hapic()


class PyramidController(object):
    @hapic.with_api_doc()
    @hapic.output_body(AboutSchema())
    def about(self, context, request):
        """
        This endpoint allow to check that the API is running. This description
        is generated from the docstring of the method.
        """
        return {
            'version': '1.2.3',
            'datetime': datetime.now(),
        }

    @hapic.with_api_doc()
    @hapic.output_body(UserDigestSchema(many=True))
    def get_users(self, context, request):
        """
        Obtain users list.
        """
        return UserLib().get_users()

    @hapic.with_api_doc()
    @hapic.handle_exception(UserNotFound, HTTPStatus.NOT_FOUND)
    @hapic.input_path(UserIdPathSchema())
    @hapic.output_body(UserSchema())
    def get_user(self, context, request, hapic_data: HapicData):
        """
        Return a user taken from the list or return a 404
        """
        return UserLib().get_user(int(hapic_data.path['id']))

    @hapic.with_api_doc()
    # TODO - G.M - 2017-12-5 - Support input_forms ?
    # TODO - G.M - 2017-12-5 - Support exclude, only ?
    @hapic.input_body(UserSchema(exclude=('id',)))
    @hapic.output_body(UserSchema())
    def add_user(self, context, request, hapic_data: HapicData):
        """
        Add a user to the list
        """
        print(hapic_data.body)
        new_user = User(**hapic_data.body)
        return UserLib().add_user(new_user)

    @hapic.with_api_doc()
    @hapic.handle_exception(UserNotFound, HTTPStatus.NOT_FOUND)
    @hapic.output_body(NoContentSchema(), default_http_code=204)
    @hapic.input_path(UserIdPathSchema())
    def del_user(self, context, request, hapic_data: HapicData):
        UserLib().del_user(int(hapic_data.path['id']))
        return NoContentSchema()

    def bind(self, configurator: Configurator):
        configurator.add_route('about', '/about', request_method='GET')
        configurator.add_view(self.about, route_name='about', renderer='json')

        configurator.add_route('get_users', '/users', request_method='GET')  # nopep8
        configurator.add_view(self.get_users, route_name='get_users', renderer='json')  # nopep8

        configurator.add_route('get_user', '/users/{id}', request_method='GET')  # nopep8
        configurator.add_view(self.get_user, route_name='get_user', renderer='json')  # nopep8

        configurator.add_route('add_user', '/users', request_method='POST')  # nopep8
        configurator.add_view(self.add_user, route_name='add_user', renderer='json')  # nopep8

        configurator.add_route('del_user', '/users/{id}', request_method='DELETE')  # nopep8
        configurator.add_view(self.del_user, route_name='del_user', renderer='json')  # nopep8


if __name__ == "__main__":
    configurator = Configurator(autocommit=True)
    controllers = PyramidController()
    controllers.bind(configurator)
    hapic.set_context(PyramidContext(configurator, default_error_builder=MarshmallowDefaultErrorBuilder()))

    print('')
    print('')
    print('GENERATING OPENAPI DOCUMENTATION')
    openapi_file_name = 'api-documentation.json'
    with open(openapi_file_name, 'w') as openapi_file_handle:
        openapi_file_handle.write(
            json.dumps(
                hapic.generate_doc(
                    title='Demo API documentation',
                    description='This documentation has been generated from '
                                'code. You can see it using swagger: '
                                'http://editor2.swagger.io/'
                )
            )
        )

    print('Documentation generated in {}'.format(openapi_file_name))
    time.sleep(1)

    print('')
    print('')
    print('RUNNING PYRAMID SERVER NOW')
    # Run app
    server = make_server('127.0.0.1', 8083, configurator.make_wsgi_app())
    server.serve_forever()
