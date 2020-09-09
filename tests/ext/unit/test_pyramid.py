# coding: utf-8
from unittest import mock

from pyramid.config import Configurator
from webtest import TestApp

from hapic import Hapic
from hapic import MarshmallowProcessor
from hapic.ext.pyramid.context import PyramidContext


class TestExtPyramid:
    def test_unit__global_exception__ok__hook_called(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)

        configurator = Configurator()
        context = PyramidContext(configurator)
        hapic.set_context(context)

        @hapic.with_api_doc()
        def divide_by_zero(*args):
            raise ZeroDivisionError()

        context.handle_exception(ZeroDivisionError, http_code=400)
        configurator.add_route("root", "/")
        configurator.add_view(divide_by_zero, route_name="root")
        app = configurator.make_wsgi_app()
        test_app = TestApp(app)

        with mock.patch.object(
            context, "global_exception_caught"
        ) as mocked_global_exception_caught:

            mocked_global_exception_caught.assert_not_called()
            test_app.get("/", status=400)
            assert mocked_global_exception_caught.call_args
