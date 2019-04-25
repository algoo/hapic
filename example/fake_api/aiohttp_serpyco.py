# coding: utf-8
from datetime import datetime
import json
import time

from aiohttp import web

from example.fake_api.schema_serpyco import AboutResponseSchema
from example.fake_api.schema_serpyco import ListsUserSchema
from example.fake_api.schema_serpyco import NoContentSchema
from example.fake_api.schema_serpyco import PaginationSchema
from example.fake_api.schema_serpyco import UserPathSchema
from example.fake_api.schema_serpyco import UserSchema
from hapic import Hapic
from hapic import HapicData
from hapic.error.serpyco import SerpycoDefaultErrorBuilder
from hapic.ext.aiohttp.context import AiohttpContext
from hapic.processor.serpyco import SerpycoProcessor

hapic = Hapic(async_=True)
hapic.set_processor_class(SerpycoProcessor)


class DictLikeObject(dict):
    def __getattr__(self, item):
        return self[item]


class AiohttpSerpycoController(object):
    @hapic.with_api_doc()
    @hapic.output_body(AboutResponseSchema)
    # FIXME BS 2018-12-13: Manage error cases (#118)
    # @hapic.handle_exception(ZeroDivisionError, http_code=400)
    async def about(self, request):
        """
        General information about this API.
        """
        return AboutResponseSchema(
            version="1.2.3", datetime=datetime(2017, 12, 7, 10, 55, 8, 488996)
        )

    @hapic.with_api_doc()
    @hapic.output_body(ListsUserSchema)
    async def get_users(self, request):
        """
        Obtain users list.
        """
        some_user = UserSchema(
            id=4,
            username="some_user",
            display_name="Damien Accorsi",
            company="Algoo",
            first_name="Damien",
            last_name="Accorsi",
            email_address="damien@local",
        )
        return ListsUserSchema(
            item_nb=1,
            items=[some_user],
            pagination=PaginationSchema(first_id=0, last_id=5, current_id=0),
        )

    @hapic.with_api_doc()
    @hapic.output_body(
        UserSchema,
        processor=SerpycoProcessor(many=True, only=["id", "username", "display_name", "company"]),
    )
    async def get_users2(self, request):
        """
        Obtain users list.
        """
        return [
            DictLikeObject(
                {
                    "id": 4,
                    "username": "some_user",
                    "display_name": "Damien Accorsi",
                    "company": "Algoo",
                }
            )
        ]

    @hapic.with_api_doc()
    @hapic.input_path(UserPathSchema)
    @hapic.output_body(UserSchema)
    async def get_user(self, request, hapic_data: HapicData):
        """
        Obtain one user
        """
        return UserSchema(
            id=4,
            username="some_user",
            email_address="some.user@hapic.com",
            first_name="Damien",
            last_name="Accorsi",
            display_name="Damien Accorsi",
            company="Algoo",
        )

    @hapic.with_api_doc()
    @hapic.input_body(UserSchema, processor=SerpycoProcessor(exclude=["id"]))
    @hapic.output_body(UserSchema)
    async def add_user(self, request, hapic_data: HapicData):
        """
        Add new user
        """
        return DictLikeObject(
            {
                "id": 4,
                "username": "some_user",
                "email_address": "some.user@hapic.com",
                "first_name": "Damien",
                "last_name": "Accorsi",
                "display_name": "Damien Accorsi",
                "company": "Algoo",
            }
        )

    @hapic.with_api_doc()
    @hapic.output_body(NoContentSchema, default_http_code=204)
    @hapic.input_path(UserPathSchema)
    async def del_user(self, request, hapic_data: HapicData):
        """
        delete user
        """

    def bind(self, app):
        """

        app.route('/about', callback=self.about)
        app.route('/users', callback=self.get_users)
        app.route('/users2', callback=self.get_users2)
        app.route('/users/<id>', callback=self.get_user)
        app.route('/users/', callback=self.add_user,  method='POST')
        app.route('/users/<id>', callback=self.del_user, method='DELETE')
        :param app:
        :return:
        """

        app.add_routes(
            [
                web.get("/about", self.about),
                web.get("/users", self.get_users),
                web.get("/users2", self.get_users2),
                web.get(r"/users/{id}", self.get_user),
                web.post("/users/", self.add_user),
                web.delete("/users/{id}", self.del_user),
            ]
        )


if __name__ == "__main__":
    app = web.Application()
    controllers = AiohttpSerpycoController()
    controllers.bind(app)
    hapic.set_context(AiohttpContext(app, default_error_builder=SerpycoDefaultErrorBuilder()))
    time.sleep(1)
    s = json.dumps(hapic.generate_doc(title="Fake API", description="just an example of hapic API"))
    time.sleep(1)
    # print swagger doc
    print(s)
    # Run app
    web.run_app(app)
