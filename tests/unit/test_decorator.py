# -*- coding: utf-8 -*-
import typing
from http import HTTPStatus

import marshmallow

from hapic.data import HapicData
from hapic.decorator import ExceptionHandlerControllerWrapper
from hapic.decorator import InputControllerWrapper
from hapic.decorator import InputOutputControllerWrapper
from hapic.decorator import OutputControllerWrapper
from hapic.hapic import ErrorResponseSchema
from hapic.processor import MarshmallowOutputProcessor
from hapic.processor import ProcessValidationError
from hapic.processor import ProcessorInterface
from hapic.processor import RequestParameters
from tests.base import Base
from tests.base import MyContext


class MyProcessor(ProcessorInterface):
    def process(self, value):
        return value + 1

    def get_validation_error(
        self,
        request_context: RequestParameters,
    ) -> ProcessValidationError:
        return ProcessValidationError(
            details={
                'original_request_context': request_context,
            },
            message='ERROR',
        )


class MyControllerWrapper(InputOutputControllerWrapper):
    def before_wrapped_func(
        self,
        func_args: typing.Tuple[typing.Any, ...],
        func_kwargs: typing.Dict[str, typing.Any],
    ) -> typing.Union[None, typing.Any]:
        if func_args and func_args[0] == 666:
            return {
                'error_response': 'we are testing'
            }

        func_kwargs['added_parameter'] = 'a value'

    def after_wrapped_function(self, response: typing.Any) -> typing.Any:
        return response * 2


class MyInputQueryControllerWrapper(InputControllerWrapper):
    def get_processed_data(
        self,
        request_parameters: RequestParameters,
    ) -> typing.Any:
        return request_parameters.query_parameters

    def update_hapic_data(
        self,
        hapic_data: HapicData,
        processed_data: typing.Dict[str, typing.Any],
    ) -> typing.Any:
        hapic_data.query = processed_data


class MySchema(marshmallow.Schema):
    name = marshmallow.fields.String(required=True)


class TestControllerWrapper(Base):
    def test_unit__base_controller_wrapper__ok__no_behaviour(self):
        context = MyContext()
        processor = MyProcessor()
        wrapper = InputOutputControllerWrapper(context, processor)

        @wrapper.get_wrapper
        def func(foo):
            return foo

        result = func(42)
        assert result == 42

    def test_unit__base_controller__ok__replaced_response(self):
        context = MyContext()
        processor = MyProcessor()
        wrapper = MyControllerWrapper(context, processor)

        @wrapper.get_wrapper
        def func(foo):
            return foo

        # see MyControllerWrapper#before_wrapped_func
        result = func(666)
        # result have been replaced by MyControllerWrapper#before_wrapped_func
        assert {'error_response': 'we are testing'} == result

    def test_unit__controller_wrapper__ok__overload_input(self):
        context = MyContext()
        processor = MyProcessor()
        wrapper = MyControllerWrapper(context, processor)

        @wrapper.get_wrapper
        def func(foo, added_parameter=None):
            # see MyControllerWrapper#before_wrapped_func
            assert added_parameter == 'a value'
            return foo

        result = func(42)
        # See MyControllerWrapper#after_wrapped_function
        assert result == 84


class TestInputControllerWrapper(Base):
    def test_unit__input_data_wrapping__ok__nominal_case(self):
        context = MyContext(fake_query_parameters={
            'foo': 'bar',
        })
        processor = MyProcessor()
        wrapper = MyInputQueryControllerWrapper(context, processor)

        @wrapper.get_wrapper
        def func(foo, hapic_data=None):
            assert hapic_data
            assert isinstance(hapic_data, HapicData)
            # see MyControllerWrapper#before_wrapped_func
            assert hapic_data.query == {'foo': 'bar'}
            return foo

        result = func(42)
        assert result == 42


class TestOutputControllerWrapper(Base):
    def test_unit__output_data_wrapping__ok__nominal_case(self):
        context = MyContext()
        processor = MyProcessor()
        wrapper = OutputControllerWrapper(context, processor)

        @wrapper.get_wrapper
        def func(foo, hapic_data=None):
            # If no use of input wrapper, no hapic_data is given
            assert not hapic_data
            return foo

        result = func(42)
        # see MyProcessor#process
        assert {
                   'http_code': HTTPStatus.OK,
                   'original_response': 43,
               } == result

    def test_unit__output_data_wrapping__fail__error_response(self):
        context = MyContext()
        processor = MarshmallowOutputProcessor()
        processor.schema = MySchema()
        wrapper = OutputControllerWrapper(context, processor)

        @wrapper.get_wrapper
        def func(foo):
            return 'wrong result format'

        result = func(42)
        # see MyProcessor#process
        assert isinstance(result, dict)
        assert 'http_code' in result
        assert result['http_code'] == HTTPStatus.INTERNAL_SERVER_ERROR
        assert 'original_error' in result
        assert result['original_error'].details == {
            'name': ['Missing data for required field.']
        }


class TestExceptionHandlerControllerWrapper(Base):
    def test_unit__exception_handled__ok__nominal_case(self):
        context = MyContext()
        wrapper = ExceptionHandlerControllerWrapper(
            ZeroDivisionError,
            context,
            schema=ErrorResponseSchema(),
            http_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

        @wrapper.get_wrapper
        def func(foo):
            raise ZeroDivisionError('We are testing')

        response = func(42)
        assert 'http_code' in response
        assert response['http_code'] == HTTPStatus.INTERNAL_SERVER_ERROR
        assert 'original_response' in response
        assert response['original_response'] == {
            'message': 'We are testing',
            'code': None,
            'detail': {},
        }

    def test_unit__exception_handled__ok__exception_error_dict(self):
        class MyException(Exception):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.error_dict = {}

        context = MyContext()
        wrapper = ExceptionHandlerControllerWrapper(
            MyException,
            context,
            schema=ErrorResponseSchema(),
            http_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

        @wrapper.get_wrapper
        def func(foo):
            exc = MyException('We are testing')
            exc.error_detail = {'foo': 'bar'}
            raise exc

        response = func(42)
        assert 'http_code' in response
        assert response['http_code'] == HTTPStatus.INTERNAL_SERVER_ERROR
        assert 'original_response' in response
        assert response['original_response'] == {
            'message': 'We are testing',
            'code': None,
            'detail': {'foo': 'bar'},
        }
