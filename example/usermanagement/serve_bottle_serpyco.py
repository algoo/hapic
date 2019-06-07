# -*- coding: utf-8 -*-

from datetime import datetime
import json
import time

import bottle

from example.usermanagement.schema_serpyco import AboutSchema
from example.usermanagement.schema_serpyco import NoContentSchema
from example.usermanagement.schema_serpyco import UserAvatarSchema
from example.usermanagement.schema_serpyco import UserDigestSchema
from example.usermanagement.schema_serpyco import UserIdPathSchema
from example.usermanagement.schema_serpyco import UserSchema
from example.usermanagement.userlib import User
from example.usermanagement.userlib import UserAvatarNotFound
from example.usermanagement.userlib import UserLib
from example.usermanagement.userlib import UserNotFound
from hapic import Hapic
from hapic.data import HapicData
from hapic.data import HapicFile
from hapic.error.serpyco import SerpycoDefaultErrorBuilder
from hapic.ext.bottle import BottleContext
from hapic.processor.serpyco import SerpycoProcessor

try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus


hapic = Hapic(async_=False)
hapic.set_processor_class(SerpycoProcessor)


class DictLikeObject(dict):
    def __getattr__(self, item):
        return self[item]


class BottleController(object):
    @hapic.with_api_doc()
    @hapic.output_body(AboutSchema)
    def about(self):
        """
        This endpoint allow to check that the API is running. This description
        is generated from the docstring of the method.
        """
        return DictLikeObject({"version": "1.2.3", "datetime": datetime.now()})

    @hapic.with_api_doc()
    @hapic.output_body(UserDigestSchema, processor=SerpycoProcessor(many=True))
    def get_users(self):
        """
        Obtain users list.
        """
        return UserLib().get_users()

    @hapic.with_api_doc()
    @hapic.handle_exception(UserNotFound, HTTPStatus.NOT_FOUND)
    @hapic.input_path(UserIdPathSchema)
    @hapic.output_body(UserSchema)
    def get_user(self, id, hapic_data: HapicData):
        """
        Return a user taken from the list or return a 404
        """
        return UserLib().get_user(int(hapic_data.path.id))

    @hapic.with_api_doc()
    # TODO - G.M - 2017-12-5 - Support input_forms ?
    # TODO - G.M - 2017-12-5 - Support exclude, only ?
    @hapic.input_body(UserSchema, processor=SerpycoProcessor(exclude=["id"]))
    @hapic.output_body(UserSchema)
    def add_user(self, hapic_data: HapicData):
        """
        Add a user to the list
        """
        new_user = User(**hapic_data.body)
        return UserLib().add_user(new_user)

    @hapic.with_api_doc()
    @hapic.handle_exception(UserNotFound, HTTPStatus.NOT_FOUND)
    @hapic.output_body(NoContentSchema, default_http_code=204)
    @hapic.input_path(UserIdPathSchema)
    def del_user(self, id, hapic_data: HapicData):
        UserLib().del_user(int(hapic_data.path.id))
        return NoContentSchema()

    @hapic.with_api_doc()
    @hapic.handle_exception(UserNotFound, HTTPStatus.NOT_FOUND)
    @hapic.handle_exception(UserAvatarNotFound, HTTPStatus.NOT_FOUND)
    @hapic.input_path(UserIdPathSchema)
    @hapic.output_file(["image/png"])
    def get_user_avatar(self, id, hapic_data: HapicData):
        return HapicFile(
            file_path=UserLib().get_user_avatar_path(user_id=(int(hapic_data.path.id)))
        )

    @hapic.with_api_doc()
    @hapic.handle_exception(UserNotFound, HTTPStatus.NOT_FOUND)
    @hapic.handle_exception(UserAvatarNotFound, HTTPStatus.BAD_REQUEST)
    @hapic.input_path(UserIdPathSchema)
    @hapic.input_files(UserAvatarSchema)
    @hapic.output_body(NoContentSchema, default_http_code=204)
    def update_user_avatar(self, id, hapic_data: HapicData):
        UserLib().update_user_avatar(
            user_id=int(hapic_data.path.id), avatar=hapic_data.files.avatar
        )

    def bind(self, app: bottle.Bottle):
        app.route("/about", callback=self.about)
        app.route("/users/", callback=self.get_users)
        app.route("/users/<id>", callback=self.get_user)
        app.route("/users/", callback=self.add_user, method="POST")
        app.route("/users/<id>", callback=self.del_user, method="DELETE")
        app.route("/users/<id>/avatar", callback=self.get_user_avatar)
        app.route("/users/<id>/avatar", callback=self.update_user_avatar, method="PUT")


if __name__ == "__main__":
    app = bottle.Bottle()
    controllers = BottleController()
    controllers.bind(app)
    hapic.set_context(BottleContext(app, default_error_builder=SerpycoDefaultErrorBuilder()))

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
    print("RUNNING BOTTLE SERVER NOW")
    print("DOCUMENTATION AVAILABLE AT /doc/")
    # Run app
    app.run(host="127.0.0.1", port=8081, debug=True)
