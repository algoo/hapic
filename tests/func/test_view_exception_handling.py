# coding: utf-8
import json

import bottle
from webtest import TestApp

from hapic import Hapic
from hapic import MarshmallowProcessor
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
from hapic.error.serpyco import SerpycoDefaultErrorBuilder
from hapic.ext.agnostic.context import AgnosticApp
from hapic.ext.agnostic.context import AgnosticContext
from hapic.processor.serpyco import SerpycoProcessor


class TestViewExceptionHandling(object):
    """
    Test view exception for each processor with build-in default processor.
    Test is made with AgnosticContext
    """

    def test_unit__handle_exception_with_default_error_builder__ok__serpyco(self):
        app = AgnosticApp()
        hapic = Hapic()
        hapic.set_processor_class(SerpycoProcessor)
        hapic.set_context(
            AgnosticContext(
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

    def test_unit__handle_exception_with_default_error_builder__ok__marshmallow(self):
        app = AgnosticApp()
        hapic = Hapic()
        hapic.set_processor_class(MarshmallowProcessor)
        hapic.set_context(
            AgnosticContext(
                app, default_error_builder=MarshmallowDefaultErrorBuilder()
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
