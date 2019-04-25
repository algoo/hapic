# -*- coding: utf-8 -*-
from hapic import Hapic
from hapic.decorator import DECORATION_ATTRIBUTE_NAME
from tests.base import Base


class TestHapic(Base):
    def test_unit__decoration__ok__simple_function(self):
        hapic = Hapic()

        @hapic.with_api_doc()
        def controller_a():
            pass

        token = getattr(controller_a, DECORATION_ATTRIBUTE_NAME, None)
        assert token

        assert hapic.controllers
        assert 1 == len(hapic.controllers)
        reference = hapic.controllers[0].reference

        assert token == reference.token
        assert controller_a == reference.wrapper
        assert controller_a != reference.wrapped

    def test_unit__decoration__ok__method(self):
        hapic = Hapic()

        class MyControllers(object):
            @hapic.with_api_doc()
            def controller_a(self):
                pass

        my_controllers = MyControllers()
        class_method_token = getattr(MyControllers.controller_a, DECORATION_ATTRIBUTE_NAME, None)
        assert class_method_token
        instance_method_token = getattr(
            my_controllers.controller_a, DECORATION_ATTRIBUTE_NAME, None
        )
        assert instance_method_token

        assert hapic.controllers
        assert 1 == len(hapic.controllers)
        reference = hapic.controllers[0].reference

        assert class_method_token == reference.token
        assert instance_method_token == reference.token

        assert MyControllers.controller_a == reference.wrapper
        assert MyControllers.controller_a != reference.wrapped
        assert my_controllers.controller_a != reference.wrapper
        assert my_controllers.controller_a != reference.wrapped
