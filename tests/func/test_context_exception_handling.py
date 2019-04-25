# coding: utf-8
import pytest
from webtest import TestApp

from hapic import Hapic
from hapic import MarshmallowProcessor
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
from hapic.ext.aiohttp.context import AiohttpContext
from hapic.ext.bottle import BottleContext
from hapic.ext.flask import FlaskContext
from hapic.ext.pyramid import PyramidContext
from tests.base import Base


class TestContextExceptionHandling(Base):
    """
    Test apply exception on all context with all different frameworks supported
    """

    @pytest.mark.asyncio
    async def test_func__catch_one_exception__ok__aiohttp_case(self, test_client):
        from aiohttp import web

        app = web.Application()
        hapic = Hapic(processor_class=MarshmallowProcessor)
        context = AiohttpContext(app=app)
        hapic.set_context(context)

        async def my_view(request):
            raise ZeroDivisionError("An exception message")

        app.add_routes([web.get("/my-view", my_view)])
        # FIXME - G.M - 17-05-2018 - Verify if:
        # - other view that work/raise an other exception do not go
        # into this code for handle this exceptions.
        # - response come clearly from there, not from web framework:
        #  Check not only http code, but also body.
        # see  issue #158 (https://github.com/algoo/hapic/issues/158)
        context.handle_exception(ZeroDivisionError, http_code=400)
        test_app = await test_client(app)
        response = await test_app.get("/my-view")

        assert 400 == response.status

    def test_func__catch_one_exception__ok__flask_case(self):
        from flask import Flask

        app = Flask(__name__)
        hapic = Hapic(processor_class=MarshmallowProcessor)
        context = FlaskContext(app=app)
        hapic.set_context(context)

        def my_view():
            raise ZeroDivisionError("An exception message")

        app.add_url_rule("/my-view", view_func=my_view, methods=["GET"])
        # FIXME - G.M - 17-05-2018 - Verify if:
        # - other view that work/raise an other exception do not go
        # into this code for handle this exceptions.
        # - response come clearly from there, not from web framework:
        #  Check not only http code, but also body.
        # see  issue #158 (https://github.com/algoo/hapic/issues/158)
        context.handle_exception(ZeroDivisionError, http_code=400)

        test_app = TestApp(app)
        response = test_app.get("/my-view", status="*")

        assert 400 == response.status_code

    def test_func__catch_one_exception__ok__bottle_case(self):
        import bottle

        app = bottle.Bottle()
        hapic = Hapic(processor_class=MarshmallowProcessor)
        context = BottleContext(app=app)
        hapic.set_context(context)

        def my_view():
            raise ZeroDivisionError("An exception message")

        app.route("/my-view", method="GET", callback=my_view)
        # FIXME - G.M - 17-05-2018 - Verify if:
        # - other view that work/raise an other exception do not go
        # into this code for handle this exceptions.
        # - response come clearly from there, not from web framework:
        #  Check not only http code, but also body.
        # see  issue #158 (https://github.com/algoo/hapic/issues/158)
        context.handle_exception(ZeroDivisionError, http_code=400)

        test_app = TestApp(app)
        response = test_app.get("/my-view", status="*")

        assert 400 == response.status_code

    def test_func__catch_one_exception__ok__pyramid(self):
        from pyramid.config import Configurator

        configurator = Configurator(autocommit=True)
        context = PyramidContext(
            configurator, default_error_builder=MarshmallowDefaultErrorBuilder()
        )
        hapic = Hapic(processor_class=MarshmallowProcessor)
        hapic.set_context(context)

        def my_view(context, request):
            raise ZeroDivisionError("An exception message")

        configurator.add_route("my_view", "/my-view", request_method="GET")
        configurator.add_view(my_view, route_name="my_view", renderer="json")

        # FIXME - G.M - 17-05-2018 - Verify if:
        # - other view that work/raise an other exception do not go
        # into this code for handle this exceptions.
        # - response come clearly from there, not from web framework:
        #  Check not only http code, but also body.
        # see  issue #158 (https://github.com/algoo/hapic/issues/158)
        context.handle_exception(ZeroDivisionError, http_code=400)

        app = configurator.make_wsgi_app()
        test_app = TestApp(app)
        response = test_app.get("/my-view", status="*")

        assert 400 == response.status_code
