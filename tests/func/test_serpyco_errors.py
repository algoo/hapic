# coding: utf-8
import json

import bottle
from webtest import TestApp

from hapic import Hapic
from hapic.error.serpyco import SerpycoDefaultErrorBuilder
from hapic.ext.bottle import BottleContext
from hapic.processor.serpyco import SerpycoProcessor


class TestSerpycoHandleException(object):
    def test_unit__handle_exception__ok__nominal_case(self):
        app = bottle.Bottle()
        hapic = Hapic()
        hapic.set_processor_class(SerpycoProcessor)
        hapic.set_context(
            BottleContext(
                app, default_error_builder=SerpycoDefaultErrorBuilder()
            )
        )

        @hapic.with_api_doc()
        @hapic.handle_exception(ZeroDivisionError, http_code=400)
        def my_view():
            1 / 0

        response = my_view()
        json_ = json.loads(response.body)
        assert {
            "code": None,
            "details": {"error_detail": {}},
            "message": "division by zero",
        } == json_

    def test_unit__handle_global_exception__ok__nominal_case(self):
        app = bottle.Bottle()
        hapic = Hapic()
        hapic.set_processor_class(SerpycoProcessor)

        context = BottleContext(
            app, default_error_builder=SerpycoDefaultErrorBuilder()
        )
        context.handle_exception(ZeroDivisionError, http_code=400)

        hapic.set_context(context)

        @hapic.with_api_doc()
        def my_view():
            1 / 0

        app.route("/hello", "GET", my_view)
        test_app = TestApp(app)

        response = test_app.get("/hello", status="*")
        assert {
            "code": None,
            "details": {"error_detail": {}},
            "message": "division by zero",
        } == response.json
