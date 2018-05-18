# -*- coding: utf-8 -*-
import json

import pytest
import typing

from hapic.exception import OutputValidationException

try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus

import marshmallow
from multidict import MultiDict

from hapic.data import HapicData
from hapic.decorator import ExceptionHandlerControllerWrapper
from hapic.decorator import InputQueryControllerWrapper
from hapic.decorator import InputControllerWrapper
from hapic.decorator import InputOutputControllerWrapper
from hapic.decorator import OutputControllerWrapper
from hapic.error import DefaultErrorBuilder
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


class MySimpleProcessor(ProcessorInterface):
    def process(self, value):
        return value

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
        context = MyContext(app=None)
        processor = MyProcessor()
        wrapper = InputOutputControllerWrapper(context, processor)

        @wrapper.get_wrapper
        def func(foo):
            return foo

        result = func(42)
        assert result == 42

    def test_unit__base_controller__ok__replaced_response(self):
        context = MyContext(app=None)
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
        context = MyContext(app=None)
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
        context = MyContext(
            app=None,
            fake_query_parameters=MultiDict(
                (
                    ('foo', 'bar',),
                )
            )
        )
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

    def test_unit__multi_query_param_values__ok__use_as_list(self):
        context = MyContext(
            app=None,
            fake_query_parameters=MultiDict(
                (
                    ('user_id', 'abc'),
                    ('user_id', 'def'),
                ),
            )
        )
        processor = MySimpleProcessor()
        wrapper = InputQueryControllerWrapper(
            context,
            processor,
            as_list=['user_id'],
        )

        @wrapper.get_wrapper
        def func(hapic_data=None):
            assert hapic_data
            assert isinstance(hapic_data, HapicData)
            # see MyControllerWrapper#before_wrapped_func
            assert ['abc', 'def'] == hapic_data.query.get('user_id')
            return hapic_data.query.get('user_id')

        result = func()
        assert result == ['abc', 'def']

    def test_unit__multi_query_param_values__ok__without_as_list(self):
        context = MyContext(
            app=None,
            fake_query_parameters=MultiDict(
                (
                    ('user_id', 'abc'),
                    ('user_id', 'def'),
                ),
            )
        )
        processor = MySimpleProcessor()
        wrapper = InputQueryControllerWrapper(
            context,
            processor,
        )

        @wrapper.get_wrapper
        def func(hapic_data=None):
            assert hapic_data
            assert isinstance(hapic_data, HapicData)
            # see MyControllerWrapper#before_wrapped_func
            assert 'abc' == hapic_data.query.get('user_id')
            return hapic_data.query.get('user_id')

        result = func()
        assert result == 'abc'


class TestOutputControllerWrapper(Base):
    def test_unit__output_data_wrapping__ok__nominal_case(self):
        context = MyContext(app=None)
        processor = MyProcessor()
        wrapper = OutputControllerWrapper(context, processor)

        @wrapper.get_wrapper
        def func(foo, hapic_data=None):
            # If no use of input wrapper, no hapic_data is given
            assert not hapic_data
            return foo

        result = func(42)
        assert HTTPStatus.OK == result.status_code
        assert '43' == result.body

    def test_unit__output_data_wrapping__fail__error_response(self):
        context = MyContext(app=None)
        processor = MarshmallowOutputProcessor()
        processor.schema = MySchema()
        wrapper = OutputControllerWrapper(context, processor)

        @wrapper.get_wrapper
        def func(foo):
            return 'wrong result format'

        result = func(42)
        assert HTTPStatus.INTERNAL_SERVER_ERROR == result.status_code
        assert {
                   'original_error': {
                       'details': {
                           'name': ['Missing data for required field.']
                       },
                       'message': 'Validation error of output data'
                   },
                   'http_code': 500,
               } == json.loads(result.body)


class TestExceptionHandlerControllerWrapper(Base):
    def test_unit__exception_handled__ok__nominal_case(self):
        context = MyContext(app=None)
        wrapper = ExceptionHandlerControllerWrapper(
            ZeroDivisionError,
            context,
            error_builder=DefaultErrorBuilder(),
            http_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

        @wrapper.get_wrapper
        def func(foo):
            raise ZeroDivisionError('We are testing')

        response = func(42)
        assert HTTPStatus.INTERNAL_SERVER_ERROR == response.status_code
        assert {
                   'details': {'error_detail': {}},
                   'message': 'We are testing',
                   'code': None,
               } == json.loads(response.body)

    def test_unit__exception_handled__ok__exception_error_dict(self):
        class MyException(Exception):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.error_dict = {}

        context = MyContext(app=None)
        wrapper = ExceptionHandlerControllerWrapper(
            MyException,
            context,
            error_builder=DefaultErrorBuilder(),
            http_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

        @wrapper.get_wrapper
        def func(foo):
            exc = MyException('We are testing')
            exc.error_detail = {'foo': 'bar'}
            raise exc

        response = func(42)
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert {
            'message': 'We are testing',
            'details': {'error_detail': {'foo': 'bar'}},
            'code': None,
        } == json.loads(response.body)

    def test_unit__exception_handler__error__error_content_malformed(self):
        class MyException(Exception):
            pass

        class MyErrorBuilder(DefaultErrorBuilder):
            def build_from_exception(
                self,
                exception: Exception,
                include_traceback: bool = False,
            ) -> dict:
                # this is not matching with DefaultErrorBuilder schema
                return {}

        context = MyContext(app=None)
        wrapper = ExceptionHandlerControllerWrapper(
            MyException,
            context,
            error_builder=MyErrorBuilder(),
        )

        def raise_it():
            raise MyException()

        wrapper = wrapper.get_wrapper(raise_it)
        with pytest.raises(OutputValidationException):
            wrapper()
