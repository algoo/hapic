# -*- coding: utf-8 -*-
import bottle

import hapic
from hapic.doc import find_bottle_route
from tests.base import Base


class TestBottleExt(Base):
    def test_unit__map_binding__ok__decorated_function(self):
        hapic_ = hapic.Hapic()
        hapic_.set_context(hapic.ext.bottle.BottleContext())

        app = bottle.Bottle()

        @hapic_.with_api_doc()
        @app.route('/')
        def controller_a():
            pass

        assert hapic_.controllers
        decoration = hapic_.controllers[0]
        route = find_bottle_route(decoration, app)

        assert route
        assert route.callback != controller_a
        assert route.callback == decoration.reference.wrapped
        assert route.callback != decoration.reference.wrapper

    def test_unit__map_binding__ok__mapped_function(self):
        hapic_ = hapic.Hapic()
        hapic_.set_context(hapic.ext.bottle.BottleContext())

        app = bottle.Bottle()

        @hapic_.with_api_doc()
        def controller_a():
            pass

        app.route('/', callback=controller_a)

        assert hapic_.controllers
        decoration = hapic_.controllers[0]
        route = find_bottle_route(decoration, app)

        assert route
        assert route.callback == controller_a
        assert route.callback == decoration.reference.wrapper
        assert route.callback != decoration.reference.wrapped

    def test_unit__map_binding__ok__mapped_method(self):
        hapic_ = hapic.Hapic()
        hapic_.set_context(hapic.ext.bottle.BottleContext())

        app = bottle.Bottle()

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
        route = find_bottle_route(decoration, app)

        assert route
        # Important note: instance controller_a method is
        # not class controller_a, so no matches with callbacks
        assert route.callback != MyControllers.controller_a
        assert route.callback != decoration.reference.wrapped
        assert route.callback != decoration.reference.wrapper
