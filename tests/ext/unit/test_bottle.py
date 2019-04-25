# -*- coding: utf-8 -*-
import bottle
from webtest import TestApp

import hapic
from hapic import MarshmallowProcessor
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
from hapic.ext.bottle import BottleContext
from tests.base import Base


class TestBottleExt(Base):
    def test_unit__map_binding__ok__decorated_function(self):
        hapic_ = hapic.Hapic(processor_class=MarshmallowProcessor)
        app = bottle.Bottle()
        context = hapic.ext.bottle.BottleContext(
            app=app, default_error_builder=MarshmallowDefaultErrorBuilder()
        )
        hapic_.set_context(context)

        @hapic_.with_api_doc()
        @app.route("/")
        def controller_a():
            pass

        assert hapic_.controllers
        decoration = hapic_.controllers[0]
        route = context.find_route(decoration)

        assert route
        assert route.original_route_object.callback != controller_a
        assert route.original_route_object.callback == decoration.reference.wrapped
        assert route.original_route_object.callback != decoration.reference.wrapper

    def test_unit__map_binding__ok__mapped_function(self):
        hapic_ = hapic.Hapic(processor_class=MarshmallowProcessor)
        app = bottle.Bottle()
        context = hapic.ext.bottle.BottleContext(
            app=app, default_error_builder=MarshmallowDefaultErrorBuilder()
        )
        hapic_.set_context(context)

        @hapic_.with_api_doc()
        def controller_a():
            pass

        app.route("/", callback=controller_a)

        assert hapic_.controllers
        decoration = hapic_.controllers[0]
        route = context.find_route(decoration)

        assert route
        assert route.original_route_object.callback == controller_a
        assert route.original_route_object.callback == decoration.reference.wrapper
        assert route.original_route_object.callback != decoration.reference.wrapped

    def test_unit__map_binding__ok__mapped_method(self):
        hapic_ = hapic.Hapic(processor_class=MarshmallowProcessor)
        app = bottle.Bottle()
        context = hapic.ext.bottle.BottleContext(
            app=app, default_error_builder=MarshmallowDefaultErrorBuilder()
        )
        hapic_.set_context(context)

        class MyControllers(object):
            def bind(self, app):
                app.route("/", callback=self.controller_a)

            @hapic_.with_api_doc()
            def controller_a(self):
                pass

        my_controllers = MyControllers()
        my_controllers.bind(app)

        assert hapic_.controllers
        decoration = hapic_.controllers[0]
        route = context.find_route(decoration)

        assert route
        # Important note: instance controller_a method is
        # not class controller_a, so no matches with callbacks
        assert route.original_route_object.callback != MyControllers.controller_a
        assert route.original_route_object.callback != decoration.reference.wrapped
        assert route.original_route_object.callback != decoration.reference.wrapper

    def test_unit__general_exception_handling__ok__nominal_case(self):
        hapic_ = hapic.Hapic(processor_class=MarshmallowProcessor)
        app = bottle.Bottle()
        context = BottleContext(app=app, default_error_builder=MarshmallowDefaultErrorBuilder())
        hapic_.set_context(context)

        def my_view():
            raise ZeroDivisionError("An exception message")

        app.route("/my-view", method="GET", callback=my_view)
        context.handle_exception(ZeroDivisionError, http_code=400)

        test_app = TestApp(app)
        response = test_app.get("/my-view", status="*")

        assert 400 == response.status_code
