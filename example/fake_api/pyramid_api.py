# -*- coding: utf-8 -*-
from datetime import datetime
import json
import time
from wsgiref.simple_server import make_server

from pyramid.config import Configurator

from example.fake_api.schema import AboutResponseSchema
from example.fake_api.schema import ListsUserSchema
from example.fake_api.schema import NoContentSchema
from example.fake_api.schema import UserPathSchema
from example.fake_api.schema import UserSchema
from hapic import Hapic
from hapic import MarshmallowProcessor
from hapic.data import HapicData
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
from hapic.ext.pyramid import PyramidContext

hapic = Hapic(processor_class=MarshmallowProcessor)


class PyramidController(object):
    @hapic.with_api_doc()
    @hapic.output_body(AboutResponseSchema())
    def about(self, context, request):
        """
        General information about this API.
        """
        return {"version": "1.2.3", "datetime": datetime(2017, 12, 7, 10, 55, 8, 488996)}

    @hapic.with_api_doc()
    @hapic.output_body(ListsUserSchema())
    def get_users(self, context, request):
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
    def get_users2(self, context, request):
        """
        Obtain users list.
        """
        return [
            {"id": 4, "username": "some_user", "display_name": "Damien Accorsi", "company": "Algoo"}
        ]

    @hapic.with_api_doc()
    @hapic.input_path(UserPathSchema())
    @hapic.output_body(UserSchema())
    def get_user(self, context, request, hapic_data: HapicData):
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
    def add_user(self, context, request, hapic_data: HapicData):
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
    def del_user(self, context, request, hapic_data: HapicData):
        """
        delete user
        """
        return NoContentSchema()

    def bind(self, configurator: Configurator):
        configurator.add_route("about", "/about", request_method="GET")
        configurator.add_view(self.about, route_name="about", renderer="json")

        configurator.add_route("get_users", "/users", request_method="GET")
        configurator.add_view(self.get_users, route_name="get_users", renderer="json")

        configurator.add_route("get_users2", "/users2", request_method="GET")
        configurator.add_view(self.get_users2, route_name="get_users2", renderer="json")

        configurator.add_route("get_user", "/users/{id}", request_method="GET")
        configurator.add_view(self.get_user, route_name="get_user", renderer="json")

        configurator.add_route("add_user", "/users/", request_method="POST")
        configurator.add_view(self.add_user, route_name="add_user", renderer="json")

        configurator.add_route("del_user", "/users/{id}", request_method="DELETE")
        configurator.add_view(self.del_user, route_name="del_user", renderer="json")


if __name__ == "__main__":
    configurator = Configurator(autocommit=True)
    controllers = PyramidController()
    controllers.bind(configurator)
    hapic.set_context(
        PyramidContext(configurator, default_error_builder=MarshmallowDefaultErrorBuilder())
    )
    time.sleep(1)
    s = json.dumps(hapic.generate_doc(title="Fake API", description="just an example of hapic API"))
    time.sleep(1)
    # print swagger doc
    print(s)
    # Run app
    server = make_server("0.0.0.0", 8083, configurator.make_wsgi_app())
    server.serve_forever()
