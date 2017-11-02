# coding: utf-8
from http import HTTPStatus

import marshmallow

from hapic import Hapic
from tests.base import Base
from tests.base import MyContext


class TestMarshmallowDecoration(Base):
    def test_unit__input_files__ok__file_is_present(self):
        hapic = Hapic()
        hapic.set_context(MyContext(fake_files_parameters={
            'file_abc': '10101010101',
        }))

        class MySchema(marshmallow.Schema):
            file_abc = marshmallow.fields.Raw(required=True)

        @hapic.with_api_doc()
        @hapic.input_files(MySchema())
        def my_controller(hapic_data=None):
            assert hapic_data
            assert hapic_data.files
            return 'OK'

        result = my_controller()
        assert 'OK' == result

    def test_unit__input_files__ok__file_is_not_present(self):
        hapic = Hapic()
        hapic.set_context(MyContext(fake_files_parameters={
            # No file here
        }))

        class MySchema(marshmallow.Schema):
            file_abc = marshmallow.fields.Raw(required=True)

        @hapic.with_api_doc()
        @hapic.input_files(MySchema())
        def my_controller(hapic_data=None):
            assert hapic_data
            assert hapic_data.files
            return 'OK'

        result = my_controller()
        assert 'http_code' in result
        assert HTTPStatus.BAD_REQUEST == result['http_code']
        assert {
                   'file_abc': ['Missing data for required field.']
               } == result['original_error'].details

    def test_unit__input_files__ok__file_is_empty_string(self):
        hapic = Hapic()
        hapic.set_context(MyContext(fake_files_parameters={
            'file_abc': '',
        }))

        class MySchema(marshmallow.Schema):
            file_abc = marshmallow.fields.Raw(required=True)

        @hapic.with_api_doc()
        @hapic.input_files(MySchema())
        def my_controller(hapic_data=None):
            assert hapic_data
            assert hapic_data.files
            return 'OK'

        result = my_controller()
        assert 'http_code' in result
        assert HTTPStatus.BAD_REQUEST == result['http_code']
        assert {'file_abc': ['Missing data for required field']} == result['original_error'].details
