# -*- coding: utf-8 -*-

from datetime import datetime
import json
import time
from wsgiref.simple_server import make_server

from pyramid.config import Configurator

from example.usermanagement.schema_marshmallow import AboutSchema
from example.usermanagement.schema_marshmallow import NoContentSchema
from example.usermanagement.schema_marshmallow import UserAvatarSchema
from example.usermanagement.schema_marshmallow import UserDigestSchema
from example.usermanagement.schema_marshmallow import UserIdPathSchema
from example.usermanagement.schema_marshmallow import UserSchema
from example.usermanagement.userlib import User
from example.usermanagement.userlib import UserAvatarNotFound
from example.usermanagement.userlib import UserLib
from example.usermanagement.userlib import UserNotFound
from hapic import Hapic
from hapic import MarshmallowProcessor
from hapic.data import HapicData
from hapic.data import HapicFile
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
from hapic.ext.pyramid import PyramidContext

try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus


hapic = Hapic()
hapic.set_processor_class(MarshmallowProcessor)


class PyramidController(object):
    @hapic.with_api_doc()
    @hapic.output_body(AboutSchema())
    def about(self, context, request):
        """
        This endpoint allow to check that the API is running. This description
        is generated from the docstring of the method.
        """
        return {"version": "1.2.3", "datetime": datetime.now()}

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
        return UserLib().get_user(int(hapic_data.path["id"]))

    @hapic.with_api_doc()
    # TODO - G.M - 2017-12-5 - Support input_forms ?
    # TODO - G.M - 2017-12-5 - Support exclude, only ?
    @hapic.input_body(UserSchema(exclude=("id",)))
    @hapic.output_body(UserSchema())
    def add_user(self, context, request, hapic_data: HapicData):
        """
        Add a user to the list
        """
        new_user = User(**hapic_data.body)
        return UserLib().add_user(new_user)

    @hapic.with_api_doc()
    @hapic.handle_exception(UserNotFound, HTTPStatus.NOT_FOUND)
    @hapic.output_body(NoContentSchema(), default_http_code=204)
    @hapic.input_path(UserIdPathSchema())
    def del_user(self, context, request, hapic_data: HapicData):
        UserLib().del_user(int(hapic_data.path["id"]))
        return NoContentSchema()

    @hapic.with_api_doc()
    @hapic.handle_exception(UserNotFound, HTTPStatus.NOT_FOUND)
    @hapic.handle_exception(UserAvatarNotFound, HTTPStatus.NOT_FOUND)
    @hapic.input_path(UserIdPathSchema())
    @hapic.output_file(["image/png"])
    def get_user_avatar(self, context, request, hapic_data: HapicData):
        return HapicFile(
            file_path=UserLib().get_user_avatar_path(user_id=(int(hapic_data.path["id"])))
        )

    @hapic.with_api_doc()
    @hapic.handle_exception(UserNotFound, HTTPStatus.NOT_FOUND)
    @hapic.handle_exception(UserAvatarNotFound, HTTPStatus.BAD_REQUEST)
    @hapic.input_path(UserIdPathSchema())
    @hapic.input_files(UserAvatarSchema())
    @hapic.output_body(NoContentSchema(), default_http_code=204)
    def update_user_avatar(self, context, request, hapic_data: HapicData):
        UserLib().update_user_avatar(
            user_id=int(hapic_data.path["id"]), avatar=hapic_data.files["avatar"]
        )

    def bind(self, configurator: Configurator):
        configurator.add_route("about", "/about", request_method="GET")
        configurator.add_view(self.about, route_name="about")

        configurator.add_route("get_users", "/users/", request_method="GET")
        configurator.add_view(self.get_users, route_name="get_users")

        configurator.add_route("get_user", "/users/{id}", request_method="GET")
        configurator.add_view(self.get_user, route_name="get_user")

        configurator.add_route("add_user", "/users/", request_method="POST")
        configurator.add_view(self.add_user, route_name="add_user")

        configurator.add_route("del_user", "/users/{id}", request_method="DELETE")
        configurator.add_view(self.del_user, route_name="del_user")

        configurator.add_route(
            "get_user_avatar", "/users/{id}/avatar", request_method="GET"
        )  # nopep8
        configurator.add_view(self.get_user_avatar, route_name="get_user_avatar")

        configurator.add_route(
            "update_user_avatar", "/users/{id}/avatar", request_method="PUT"
        )  # nopep8
        configurator.add_view(self.update_user_avatar, route_name="update_user_avatar")


if __name__ == "__main__":
    configurator = Configurator(autocommit=True)
    controllers = PyramidController()
    controllers.bind(configurator)
    hapic.set_context(
        PyramidContext(configurator, default_error_builder=MarshmallowDefaultErrorBuilder())
    )

    print("")
    print("")
    print("GENERATING OPENAPI DOCUMENTATION")

    doc_title = "Demo API documentation"
    doc_description = (
        "This documentation has been generated from "
        "code. You can see it using swagger: "
        "http://editor2.swagger.io/"
    )
    hapic.add_documentation_view("/doc/", doc_title, doc_description)
    openapi_file_name = "api-documentation.json"
    with open(openapi_file_name, "w") as openapi_file_handle:
        openapi_file_handle.write(
            json.dumps(hapic.generate_doc(title=doc_title, description=doc_description))
        )

    print("Documentation generated in {}".format(openapi_file_name))
    time.sleep(1)

    print("")
    print("")
    print("RUNNING PYRAMID SERVER NOW")
    print("DOCUMENTATION AVAILABLE AT /doc/")
    # Run app
    server = make_server("127.0.0.1", 8083, configurator.make_wsgi_app())
    server.serve_forever()
