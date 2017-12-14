# -*- coding: utf-8 -*-
import bottle

import hapic
from tests.base import Base


class TestBottleExt(Base):
    def test_unit__map_binding__ok__decorated_function(self):
        hapic_ = hapic.Hapic()
        app = bottle.Bottle()
        context = hapic.ext.bottle.BottleContext(app=app)
        hapic_.set_context(context)

        @hapic_.with_api_doc()
        @app.route('/')
        def controller_a():
            pass

        assert hapic_.controllers
        decoration = hapic_.controllers[0]
        route = context.find_route(decoration)

        assert route
        assert route.original_route_object.callback != controller_a
        assert route.original_route_object.callback == decoration.reference.wrapped  # nopep8
        assert route.original_route_object.callback != decoration.reference.wrapper  # nopep8

    def test_unit__map_binding__ok__mapped_function(self):
        hapic_ = hapic.Hapic()
        app = bottle.Bottle()
        context = hapic.ext.bottle.BottleContext(app=app)
        hapic_.set_context(context)

        @hapic_.with_api_doc()
        def controller_a():
            pass

        app.route('/', callback=controller_a)

        assert hapic_.controllers
        decoration = hapic_.controllers[0]
        route = context.find_route(decoration)

        assert route
        assert route.original_route_object.callback == controller_a
        assert route.original_route_object.callback == decoration.reference.wrapper  # nopep8
        assert route.original_route_object.callback != decoration.reference.wrapped  # nopep8

    def test_unit__map_binding__ok__mapped_method(self):
        hapic_ = hapic.Hapic()
        app = bottle.Bottle()
        context = hapic.ext.bottle.BottleContext(app=app)
        hapic_.set_context(context)

        class MyControllers(object):
            def bind(self, app):
                app.route('/', callback=self.controller_a)

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
        assert route.original_route_object.callback != MyControllers.controller_a  # nopep8
        assert route.original_route_object.callback != decoration.reference.wrapped  # nopep8
        assert route.original_route_object.callback != decoration.reference.wrapper  # nopep8
