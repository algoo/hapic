# -*- coding: utf-8 -*-
import json
from http import HTTPStatus

import flask
import time
from datetime import datetime
import hapic
from example.fake_api.schema import *
from hapic.data import HapicData


class NoContentException(Exception):
    pass


class Controllers(object):
    @hapic.with_api_doc()
    @hapic.output_body(AboutResponseSchema())
    def about(self):
        """
        General information about this API.
        """
        return {
            'version': '1.2.3',
            'datetime': datetime.now(),
        }

    @hapic.with_api_doc()
    @hapic.output_body(ListsUserSchema())
    def get_users(self):
        """
        Obtain users list.
        """
        return {
            'item_nb': 1,
            'items': [
                {
                    'id': 4,
                    'username': 'some_user',
                    'display_name': 'Damien Accorsi',
                    'company': 'Algoo',
                },
            ],
            'pagination': {
                'first_id': 0,
                'last_id': 5,
                'current_id': 0,
            }
        }

    @hapic.with_api_doc()
    @hapic.input_path(UserPathSchema())
    @hapic.output_body(UserSchema())
    def get_user(self, id, hapic_data: HapicData):
        """
        Obtain one user
        """
        return {
             'id': 4,
             'username': 'some_user',
             'email_address': 'some.user@hapic.com',
             'first_name': 'Damien',
             'last_name': 'Accorsi',
             'display_name': 'Damien Accorsi',
             'company': 'Algoo',
        }

    @hapic.with_api_doc()
    # TODO - G.M - 2017-12-5 - Support input_forms ?
    # TODO - G.M - 2017-12-5 - Support exclude, only ?
    @hapic.input_body(UserSchema(exclude=('id',)))
    @hapic.output_body(UserSchema())
    def add_user(self, hapic_data: HapicData):
        """
        Add new user
        """
        return {
             'id': 4,
             'username': 'some_user',
             'email_address': 'some.user@hapic.com',
             'first_name': 'Damien',
             'last_name': 'Accorsi',
             'display_name': 'Damien Accorsi',
             'company': 'Algoo',
        }

    @hapic.with_api_doc()
    @hapic.handle_exception(NoContentException, http_code=HTTPStatus.NO_CONTENT)
    @hapic.input_path(UserPathSchema())
    def del_user(self, id, hapic_data: HapicData):
        """
        delete user
        """

        # TODO - G.M - 2017-12-05 - Add better
        #  way to doc response of this function, using response object ?
        # return flask.Response(
        #     status=204,
        # )
        raise NoContentException

    def bind(self, app: flask.Flask):
        app.add_url_rule('/about',
                         view_func=self.about)
        app.add_url_rule('/users',
                         view_func=self.get_users)
        app.add_url_rule('/users/<id>',
                         view_func=self.get_user)
        app.add_url_rule('/users/',
                         view_func=self.add_user,
                         methods=['POST'])
        app.add_url_rule('/users/<id>',
                         view_func=self.del_user,
                         methods=['DELETE'])


app = flask.Flask(__name__)
controllers = Controllers()
controllers.bind(app)
hapic.set_context(hapic.ext.flask.FlaskContext(app))
time.sleep(1)
s = json.dumps(hapic.generate_doc())
time.sleep(1)
# print swagger doc
print(s)
# Run app
app.run(host='localhost', port=8082, debug=True)
