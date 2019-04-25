# -*- coding: utf-8 -*-
from datetime import datetime
import json
import time

import flask

from example.fake_api.schema import AboutResponseSchema
from example.fake_api.schema import ListsUserSchema
from example.fake_api.schema import NoContentSchema
from example.fake_api.schema import UserPathSchema
from example.fake_api.schema import UserSchema
from hapic import Hapic
from hapic import MarshmallowProcessor
from hapic.data import HapicData
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
from hapic.ext.flask import FlaskContext

hapic = Hapic(processor_class=MarshmallowProcessor)


class FlaskController(object):
    @hapic.with_api_doc()
    @hapic.output_body(AboutResponseSchema())
    def about(self):
        """
        General information about this API.
        """
        return {"version": "1.2.3", "datetime": datetime(2017, 12, 7, 10, 55, 8, 488996)}

    @hapic.with_api_doc()
    @hapic.output_body(ListsUserSchema())
    def get_users(self):
        """
        Obtain users list.
        """
        return {
            "item_nb": 1,
            "items": [
                {
                    "id": 4,
                    "username": "some_user",
                    "display_name": "Damien Accorsi",
                    "company": "Algoo",
                }
            ],
            "pagination": {"first_id": 0, "last_id": 5, "current_id": 0},
        }

    @hapic.with_api_doc()
    @hapic.output_body(UserSchema(many=True, only=("id", "username", "display_name", "company")))
    def get_users2(self):
        """
        Obtain users list.
        """
        return [
            {"id": 4, "username": "some_user", "display_name": "Damien Accorsi", "company": "Algoo"}
        ]

    @hapic.with_api_doc()
    @hapic.input_path(UserPathSchema())
    @hapic.output_body(UserSchema())
    def get_user(self, id, hapic_data: HapicData):
        """
        Obtain one user
        """
        return {
            "id": 4,
            "username": "some_user",
            "email_address": "some.user@hapic.com",
            "first_name": "Damien",
            "last_name": "Accorsi",
            "display_name": "Damien Accorsi",
            "company": "Algoo",
        }

    @hapic.with_api_doc()
    # TODO - G.M - 2017-12-5 - Support input_forms ?
    # TODO - G.M - 2017-12-5 - Support exclude, only ?
    @hapic.input_body(UserSchema(exclude=("id",)))
    @hapic.output_body(UserSchema())
    def add_user(self, hapic_data: HapicData):
        """
        Add new user
        """
        return {
            "id": 4,
            "username": "some_user",
            "email_address": "some.user@hapic.com",
            "first_name": "Damien",
            "last_name": "Accorsi",
            "display_name": "Damien Accorsi",
            "company": "Algoo",
        }

    @hapic.with_api_doc()
    @hapic.output_body(NoContentSchema(), default_http_code=204)
    @hapic.input_path(UserPathSchema())
    def del_user(self, id, hapic_data: HapicData):
        """
        delete user
        """
        resp = flask.Response(status=204)
        # See tests.func.fake_api.test_flask.test_func_flask_fake_api
        del resp.headers["Content-Type"]
        return resp

    def bind(self, app: flask.Flask):
        app.add_url_rule("/about", view_func=self.about)
        app.add_url_rule("/users", view_func=self.get_users)
        app.add_url_rule("/users2", view_func=self.get_users2)
        app.add_url_rule("/users/<id>", view_func=self.get_user)
        app.add_url_rule("/users/", view_func=self.add_user, methods=["POST"])
        app.add_url_rule("/users/<id>", view_func=self.del_user, methods=["DELETE"])


if __name__ == "__main__":
    app = flask.Flask(__name__)
    controllers = FlaskController()
    controllers.bind(app)
    hapic.set_context(FlaskContext(app, default_error_builder=MarshmallowDefaultErrorBuilder()))
    time.sleep(1)
    s = json.dumps(hapic.generate_doc(title="Fake API", description="just an example of hapic API"))
    time.sleep(1)
    # print swagger doc
    print(s)
    # Run app
    app.run(host="localhost", port=8082, debug=True)
