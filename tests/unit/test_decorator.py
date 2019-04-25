# -*- coding: utf-8 -*-
import json
import typing

from apispec import BasePlugin
import marshmallow
from multidict import MultiDict
import pytest

from hapic.data import HapicData
from hapic.decorator import ExceptionHandlerControllerWrapper
from hapic.decorator import InputControllerWrapper
from hapic.decorator import InputOutputControllerWrapper
from hapic.decorator import InputQueryControllerWrapper
from hapic.decorator import OutputControllerWrapper
from hapic.error.main import ErrorBuilderInterface
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
from hapic.exception import OutputValidationException
from hapic.ext.agnostic.context import AgnosticContext
from hapic.processor.main import Processor
from hapic.processor.main import ProcessValidationError
from hapic.processor.main import RequestParameters
from hapic.processor.marshmallow import MarshmallowProcessor
from tests.base import Base

try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus


if typing.TYPE_CHECKING:
    from hapic.type import TYPE_SCHEMA


class MyProcessor(Processor):
    @classmethod
    def get_default_error_builder(cls) -> ErrorBuilderInterface:
        return MarshmallowDefaultErrorBuilder()

    @classmethod
    def generate_schema_ref(cls, main_plugin: BasePlugin, schema: "TYPE_SCHEMA") -> dict:
        pass

    def get_input_files_validation_error(
        self, data_to_validate: typing.Any
    ) -> ProcessValidationError:
        pass

    def load_files_input(self, input_data: typing.Any) -> typing.Any:
        pass

    def clean_data(self, raw_data: typing.Any) -> dict:
        pass

    @classmethod
    def create_apispec_plugin(cls, schema_name_resolver: typing.Optional[typing.Callable] = None):
        pass

    def get_input_validation_error(self, data_to_validate: typing.Any) -> ProcessValidationError:
        return ProcessValidationError(details={}, message="ERROR")

    def get_output_validation_error(self, data_to_validate: typing.Any) -> ProcessValidationError:
        return ProcessValidationError(details={}, message="ERROR")

    def get_output_file_validation_error(
        self, data_to_validate: typing.Any
    ) -> ProcessValidationError:
        return ProcessValidationError(details={}, message="ERROR")

    def load(self, input_data: typing.Any) -> typing.Any:
        if isinstance(input_data, int):
            return input_data + 1
        return input_data

    def dump(self, output_data: typing.Any) -> typing.Union[typing.Dict, typing.List]:
        if isinstance(output_data, int):
            return output_data + 1
        return output_data

    def dump_output_file(self, output_file: typing.Any) -> typing.Any:
        pass


class MySimpleProcessor(MyProcessor):
    def load_input(self, input_data: typing.Any) -> typing.Any:
        return input_data

    def dump_output(self, output_data: typing.Any) -> typing.Union[typing.Dict, typing.List]:
        return output_data


class MyControllerWrapper(InputOutputControllerWrapper):
    def before_wrapped_func(
        self, func_args: typing.Tuple[typing.Any, ...], func_kwargs: typing.Dict[str, typing.Any]
    ) -> typing.Union[None, typing.Any]:
        if func_args and func_args[0] == 666:
            return {"error_response": "we are testing"}

        func_kwargs["added_parameter"] = "a value"

    def after_wrapped_function(self, response: typing.Any) -> typing.Any:
        return response * 2


class MyInputQueryControllerWrapper(InputControllerWrapper):
    def get_processed_data(self, request_parameters: RequestParameters) -> typing.Any:
        return request_parameters.query_parameters

    def update_hapic_data(
        self, hapic_data: HapicData, processed_data: typing.Dict[str, typing.Any]
    ) -> typing.Any:
        hapic_data.query = processed_data


class MySchema(marshmallow.Schema):
    name = marshmallow.fields.String(required=True)


class TestControllerWrapper(Base):
    def test_unit__base_controller_wrapper__ok__no_behaviour(self):
        context = AgnosticContext(app=None)
        processor = MyProcessor()
        wrapper = InputOutputControllerWrapper(context, lambda: processor)

        @wrapper.get_wrapper
        def func(foo):
            return foo

        result = func(42)
        assert result == 42

    def test_unit__base_controller__ok__replaced_response(self):
        context = AgnosticContext(app=None)
        processor = MyProcessor()
        wrapper = MyControllerWrapper(context, lambda: processor)

        @wrapper.get_wrapper
        def func(foo):
            return foo

        # see MyControllerWrapper#before_wrapped_func
        result = func(666)
        # result have been replaced by MyControllerWrapper#before_wrapped_func
        assert {"error_response": "we are testing"} == result

    def test_unit__controller_wrapper__ok__overload_input(self):
        context = AgnosticContext(app=None)
        processor = MyProcessor()
        wrapper = MyControllerWrapper(context, lambda: processor)

        @wrapper.get_wrapper
        def func(foo, added_parameter=None):
            # see MyControllerWrapper#before_wrapped_func
            assert added_parameter == "a value"
            return foo

        result = func(42)
        # See MyControllerWrapper#after_wrapped_function
        assert result == 84


class TestInputControllerWrapper(Base):
    def test_unit__input_data_wrapping__ok__nominal_case(self):
        context = AgnosticContext(app=None, query_parameters=MultiDict((("foo", "bar"),)))
        processor = MyProcessor()
        wrapper = MyInputQueryControllerWrapper(context, lambda: processor)

        @wrapper.get_wrapper
        def func(foo, hapic_data=None):
            assert hapic_data
            assert isinstance(hapic_data, HapicData)
            # see MyControllerWrapper#before_wrapped_func
            assert hapic_data.query == {"foo": "bar"}
            return foo

        result = func(42)
        assert result == 42

    def test_unit__multi_query_param_values__ok__use_as_list(self):
        context = AgnosticContext(
            app=None, query_parameters=MultiDict((("user_id", "abc"), ("user_id", "def")))
        )
        processor = MySimpleProcessor()
        wrapper = InputQueryControllerWrapper(context, lambda: processor, as_list=["user_id"])

        @wrapper.get_wrapper
        def func(hapic_data=None):
            assert hapic_data
            assert isinstance(hapic_data, HapicData)
            # see MyControllerWrapper#before_wrapped_func
            assert ["abc", "def"] == hapic_data.query.get("user_id")
            return hapic_data.query.get("user_id")

        result = func()
        assert result == ["abc", "def"]

    def test_unit__multi_query_param_values__ok__without_as_list(self):
        context = AgnosticContext(
            app=None, query_parameters=MultiDict((("user_id", "abc"), ("user_id", "def")))
        )
        processor = MySimpleProcessor()
        wrapper = InputQueryControllerWrapper(context, lambda: processor)

        @wrapper.get_wrapper
        def func(hapic_data=None):
            assert hapic_data
            assert isinstance(hapic_data, HapicData)
            # see MyControllerWrapper#before_wrapped_func
            assert "abc" == hapic_data.query.get("user_id")
            return hapic_data.query.get("user_id")

        result = func()
        assert result == "abc"


class TestOutputControllerWrapper(Base):
    def test_unit__output_data_wrapping__ok__nominal_case(self):
        context = AgnosticContext(app=None)
        processor = MyProcessor()
        wrapper = OutputControllerWrapper(context, lambda: processor)

        @wrapper.get_wrapper
        def func(foo, hapic_data=None):
            # If no use of input wrapper, no hapic_data is given
            assert not hapic_data
            return foo

        result = func(42)
        assert HTTPStatus.OK == result.status_code
        assert "43" == result.body

    def test_unit__output_data_wrapping__fail__error_response(self):
        context = AgnosticContext(app=None)
        processor = MarshmallowProcessor()
        processor.set_schema(MySchema())
        wrapper = OutputControllerWrapper(context, lambda: processor)

        @wrapper.get_wrapper
        def func(foo):
            return "wrong result format"

        result = func(42)
        assert HTTPStatus.INTERNAL_SERVER_ERROR == result.status_code
        assert {
            "original_error": {
                "details": {"name": ["Missing data for required field."]},
                "message": "Validation error of output data",
            },
            "http_code": 500,
        } == json.loads(result.body)


class TestExceptionHandlerControllerWrapper(Base):
    def test_unit__exception_handled__ok__nominal_case(self):
        context = AgnosticContext(app=None)
        error_builder = MarshmallowDefaultErrorBuilder()
        wrapper = ExceptionHandlerControllerWrapper(
            ZeroDivisionError,
            context,
            error_builder=error_builder,
            http_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            processor_factory=lambda schema_: MarshmallowProcessor(error_builder.get_schema()),
        )

        @wrapper.get_wrapper
        def func(foo):
            raise ZeroDivisionError("We are testing")

        response = func(42)
        assert HTTPStatus.INTERNAL_SERVER_ERROR == response.status_code
        assert {
            "details": {"error_detail": {}},
            "message": "We are testing",
            "code": None,
        } == json.loads(response.body)

    def test_unit__exception_handled__ok__exception_error_dict(self):
        class MyException(Exception):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.error_dict = {}

        context = AgnosticContext(app=None)
        error_builder = MarshmallowDefaultErrorBuilder()
        wrapper = ExceptionHandlerControllerWrapper(
            MyException,
            context,
            error_builder=error_builder,
            http_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            processor_factory=lambda schema_: MarshmallowProcessor(error_builder.get_schema()),
        )

        @wrapper.get_wrapper
        def func(foo):
            exc = MyException("We are testing")
            exc.error_detail = {"foo": "bar"}
            raise exc

        response = func(42)
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert {
            "message": "We are testing",
            "details": {"error_detail": {"foo": "bar"}},
            "code": None,
        } == json.loads(response.body)

    def test_unit__exception_handler__error__error_content_malformed(self):
        class MyException(Exception):
            pass

        class MyErrorBuilder(MarshmallowDefaultErrorBuilder):
            def build_from_exception(
                self, exception: Exception, include_traceback: bool = False
            ) -> dict:
                # this is not matching with DefaultErrorBuilder schema
                return {}

        context = AgnosticContext(app=None)
        error_builder = MyErrorBuilder()
        wrapper = ExceptionHandlerControllerWrapper(
            MyException,
            context,
            error_builder=error_builder,
            processor_factory=lambda schema_: MarshmallowProcessor(error_builder.get_schema()),
        )

        def raise_it():
            raise MyException()

        wrapper = wrapper.get_wrapper(raise_it)
        with pytest.raises(OutputValidationException):
            wrapper()
