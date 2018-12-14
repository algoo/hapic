# coding: utf-8
import bottle
from pyramid.config import Configurator
from webtest import TestApp

from hapic import Hapic
from hapic.ext.pyramid import PyramidContext
from tests.base import Base
from tests.base import MyContext


class TestExceptionHandling(Base):
    def test_func__catch_one_exception__ok__nominal_case(self):
        hapic = Hapic()
        # TODO BS 2018-05-04: Make this test non-bottle
        app = bottle.Bottle()
        context = MyContext(app=app)
        hapic.set_context(context)

        def my_view():
            raise ZeroDivisionError("An exception message")

        app.route("/my-view", method="GET", callback=my_view)
        # FIXME - G.M - 17-05-2018 - Verify if:
        # - other view that work/raise an other exception do not go
        # into this code for handle this exceptions.
        # - response come clearly from there, not from web framework:
        #  Check not only http code, but also body.
        context.handle_exception(ZeroDivisionError, http_code=400)

        test_app = TestApp(app)
        response = test_app.get("/my-view", status="*")

        assert 400 == response.status_code

    def test_func__catch_one_exception__ok__pyramid(self):
        # TODO - G.M - 17-05-2018 - Move/refactor this test
        # in order to have here only framework agnostic test
        # and framework_specific
        # test somewhere else.
        hapic = Hapic()
        configurator = Configurator(autocommit=True)
        context = PyramidContext(configurator)
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
        context.handle_exception(ZeroDivisionError, http_code=400)

        app = configurator.make_wsgi_app()
        test_app = TestApp(app)
        response = test_app.get("/my-view", status="*")

        assert 400 == response.status_code
