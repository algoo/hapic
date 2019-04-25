# coding: utf-8
import json

import marshmallow

from hapic import Hapic
from hapic import MarshmallowProcessor
from hapic.ext.agnostic.context import AgnosticContext
from tests.base import Base

try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus


class TestMarshmallowDecoration(Base):
    def test_unit__input_files__ok__file_is_present(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        hapic.set_context(AgnosticContext(app=None, files_parameters={"file_abc": "10101010101"}))

        class MySchema(marshmallow.Schema):
            file_abc = marshmallow.fields.Raw(required=True)

        @hapic.input_files(MySchema())
        def my_controller(hapic_data=None):
            assert hapic_data
            assert hapic_data.files
            return "OK"

        result = my_controller()
        assert "OK" == result

    def test_unit__input_files__ok__file_is_not_present(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        hapic.set_context(
            AgnosticContext(
                app=None,
                files_parameters={
                    # No file here
                },
            )
        )

        class MySchema(marshmallow.Schema):
            file_abc = marshmallow.fields.Raw(required=True)

        @hapic.input_files(MySchema())
        def my_controller(hapic_data=None):
            assert hapic_data
            assert hapic_data.files
            return "OK"

        result = my_controller()
        assert HTTPStatus.BAD_REQUEST == result.status_code
        assert {
            "http_code": 400,
            "original_error": {
                "details": {"file_abc": ["Missing data for required field"]},
                "message": "Validation error of input data",
            },
        } == json.loads(result.body)

    def test_unit__input_files__ok__file_is_empty_string(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        hapic.set_context(AgnosticContext(app=None, files_parameters={"file_abc": ""}))

        class MySchema(marshmallow.Schema):
            file_abc = marshmallow.fields.Raw(required=True)

        @hapic.input_files(MySchema())
        def my_controller(hapic_data=None):
            assert hapic_data
            assert hapic_data.files
            return "OK"

        result = my_controller()
        assert HTTPStatus.BAD_REQUEST == result.status_code
        assert {
            "http_code": 400,
            "original_error": {
                "details": {"file_abc": ["Missing data for required field"]},
                "message": "Validation error of input data",
            },
        } == json.loads(result.body)
