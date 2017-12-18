# -*- coding: utf-8 -*-

from datetime import datetime
try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus
import json
import flask
import time
from wsgiref.simple_server import make_server

from hapic import Hapic
from hapic.data import HapicData
from hapic.ext.flask import FlaskContext

from example.usermanagement.schema import AboutSchema
from example.usermanagement.schema import NoContentSchema
from example.usermanagement.schema import UserDigestSchema
from example.usermanagement.schema import UserIdPathSchema
from example.usermanagement.schema import UserSchema

from example.usermanagement.userlib import User
from example.usermanagement.userlib import UserLib
from example.usermanagement.userlib import UserNotFound

hapic = Hapic()


class FlaskController(object):
    @hapic.with_api_doc()
    @hapic.output_body(AboutSchema())
    def about(self):
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
    def get_users(self):
        """
        Obtain users list.
        """
        return UserLib().get_users()

    @hapic.with_api_doc()
    @hapic.handle_exception(UserNotFound, HTTPStatus.NOT_FOUND)
    @hapic.input_path(UserIdPathSchema())
    @hapic.output_body(UserSchema())
    def get_user(self, id, hapic_data: HapicData):
        """
        Return a user taken from the list or return a 404
        """
        return UserLib().get_user(int(hapic_data.path['id']))

    @hapic.with_api_doc()
    # TODO - G.M - 2017-12-5 - Support input_forms ?
    # TODO - G.M - 2017-12-5 - Support exclude, only ?
    @hapic.input_body(UserSchema(exclude=('id',)))
    @hapic.output_body(UserSchema())
    def add_user(self, hapic_data: HapicData):
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
    def del_user(self, id, hapic_data: HapicData):
        UserLib().del_user(int(hapic_data.path['id']))
        return NoContentSchema()

    def bind(self, app: flask.Flask):
        app.add_url_rule('/about', view_func=self.about)
        app.add_url_rule('/users', view_func=self.get_users)
        app.add_url_rule('/users/<id>', view_func=self.get_user)
        app.add_url_rule('/users/', view_func=self.add_user, methods=['POST'])
        app.add_url_rule('/users/<id>', view_func=self.del_user, methods=['DELETE'])  # nopep8


if __name__ == "__main__":
    app = flask.Flask(__name__)
    controllers = FlaskController()
    controllers.bind(app)
    hapic.set_context(FlaskContext(app))

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
    print('RUNNING FLASK SERVER NOW')
    # Run app
    app.run(host='127.0.0.1', port=8082, debug=True)
