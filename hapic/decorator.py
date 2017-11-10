# -*- coding: utf-8 -*-
import functools
import typing
from http import HTTPStatus

# TODO BS 20171010: bottle specific !  # see #5
import marshmallow
from bottle import HTTPResponse

from hapic.data import HapicData
from hapic.description import ControllerDescription
from hapic.exception import ProcessException
from hapic.context import ContextInterface
from hapic.processor import ProcessorInterface
from hapic.processor import RequestParameters

# TODO: Ensure usage of DECORATION_ATTRIBUTE_NAME is documented and
# var names correctly choose.  see #6
DECORATION_ATTRIBUTE_NAME = '_hapic_decoration_token'


class ControllerReference(object):
    def __init__(
        self,
        wrapper: typing.Callable[..., typing.Any],
        wrapped: typing.Callable[..., typing.Any],
        token: str,
    ) -> None:
        """
        This class is a centralization of different ways to match
        final controller with decorated function:
          - wrapper will match if final controller is the hapic returned
            wrapper
          - wrapped will match if final controller is the controller itself
          - token will match if only apposed token still exist: This case
            happen when hapic decoration is make on class function and final
            controller is the same function but as instance function.

        :param wrapper: Wrapper returned by decorator
        :param wrapped: Function wrapped by decorator
        :param token: String token set on these both functions
        """
        self.wrapper = wrapper
        self.wrapped = wrapped
        self.token = token


class ControllerWrapper(object):
    def before_wrapped_func(
        self,
        func_args: typing.Tuple[typing.Any, ...],
        func_kwargs: typing.Dict[str, typing.Any],
    ) -> typing.Union[None, typing.Any]:
        pass

    def after_wrapped_function(self, response: typing.Any) -> typing.Any:
        return response

    def get_wrapper(
        self,
        func: 'typing.Callable[..., typing.Any]',
    ) -> 'typing.Callable[..., typing.Any]':
        def wrapper(*args, **kwargs) -> typing.Any:
            # Note: Design of before_wrapped_func can be to update kwargs
            # by reference here
            replacement_response = self.before_wrapped_func(args, kwargs)
            if replacement_response:
                return replacement_response

            response = self._execute_wrapped_function(func, args, kwargs)
            new_response = self.after_wrapped_function(response)
            return new_response
        return functools.update_wrapper(wrapper, func)

    def _execute_wrapped_function(
        self,
        func,
        func_args,
        func_kwargs,
    ) -> typing.Any:
        return func(*func_args, **func_kwargs)


class InputOutputControllerWrapper(ControllerWrapper):
    def __init__(
        self,
        context: typing.Union[ContextInterface, typing.Callable[[], ContextInterface]],  # nopep8
        processor: ProcessorInterface,
        error_http_code: HTTPStatus=HTTPStatus.BAD_REQUEST,
        default_http_code: HTTPStatus=HTTPStatus.OK,
    ) -> None:
        self._context = context
        self.processor = processor
        self.error_http_code = error_http_code
        self.default_http_code = default_http_code

    @property
    def context(self) -> ContextInterface:
        if callable(self._context):
            return self._context()
        return self._context


class InputControllerWrapper(InputOutputControllerWrapper):
    def before_wrapped_func(
        self,
        func_args: typing.Tuple[typing.Any, ...],
        func_kwargs: typing.Dict[str, typing.Any],
    ) -> typing.Any:
        # Retrieve hapic_data instance or create new one
        # hapic_data is given though decorators
        # Important note here: func_kwargs is update by reference !
        hapic_data = self.ensure_hapic_data(func_kwargs)
        request_parameters = self.get_request_parameters(
            func_args,
            func_kwargs,
        )

        try:
            processed_data = self.get_processed_data(request_parameters)
            self.update_hapic_data(hapic_data, processed_data)
        except ProcessException:
            error_response = self.get_error_response(request_parameters)
            return error_response

    @classmethod
    def ensure_hapic_data(
        cls,
        func_kwargs: typing.Dict[str, typing.Any],
    ) -> HapicData:
        # TODO: Permit other name than "hapic_data" ? see #7
        try:
            return func_kwargs['hapic_data']
        except KeyError:
            hapic_data = HapicData()
            func_kwargs['hapic_data'] = hapic_data
            return hapic_data

    def get_request_parameters(
        self,
        func_args: typing.Tuple[typing.Any, ...],
        func_kwargs: typing.Dict[str, typing.Any],
    ) -> RequestParameters:
        return self.context.get_request_parameters(
            *func_args,
            **func_kwargs
        )

    def get_processed_data(
        self,
        request_parameters: RequestParameters,
    ) -> typing.Any:
        parameters_data = self.get_parameters_data(request_parameters)
        processed_data = self.processor.process(parameters_data)
        return processed_data

    def get_parameters_data(self, request_parameters: RequestParameters) -> dict:
        raise NotImplementedError()

    def update_hapic_data(
        self,
        hapic_data: HapicData,
        processed_data: typing.Dict[str, typing.Any],
    ) -> None:
        raise NotImplementedError()

    def get_error_response(
        self,
        request_parameters: RequestParameters,
    ) -> typing.Any:
        parameters_data = self.get_parameters_data(request_parameters)
        error = self.processor.get_validation_error(parameters_data)
        error_response = self.context.get_validation_error_response(
            error,
            http_code=self.error_http_code,
        )
        return error_response


class OutputControllerWrapper(InputOutputControllerWrapper):
    def __init__(
        self,
        context: typing.Union[ContextInterface, typing.Callable[[], ContextInterface]],  # nopep8
        processor: ProcessorInterface,
        error_http_code: HTTPStatus=HTTPStatus.INTERNAL_SERVER_ERROR,
        default_http_code: HTTPStatus=HTTPStatus.OK,
    ) -> None:
        super().__init__(
            context,
            processor,
            error_http_code,
            default_http_code,
        )

    def get_error_response(
        self,
        response: typing.Any,
    ) -> typing.Any:
        error = self.processor.get_validation_error(response)
        error_response = self.context.get_validation_error_response(
            error,
            http_code=self.error_http_code,
        )
        return error_response

    def after_wrapped_function(self, response: typing.Any) -> typing.Any:
        try:
            if isinstance(response, HTTPResponse):
                return response

            processed_response = self.processor.process(response)
            prepared_response = self.context.get_response(
                processed_response,
                self.default_http_code,
            )
            return prepared_response
        except ProcessException:
            # TODO: ici ou ailleurs: il faut pas forcement donner le detail
            # de l'erreur (mode debug par exemple)  see #8
            error_response = self.get_error_response(response)
            return error_response


class DecoratedController(object):
    def __init__(
        self,
        reference: ControllerReference,
        description: ControllerDescription,
        name: str='',
    ) -> None:
        self._reference = reference
        self._description = description
        self._name = name

    @property
    def reference(self) -> ControllerReference:
        return self._reference

    @property
    def description(self) -> ControllerDescription:
        return self._description

    @property
    def name(self) -> str:
        return self._name


class OutputBodyControllerWrapper(OutputControllerWrapper):
    pass


class OutputHeadersControllerWrapper(OutputControllerWrapper):
    pass


class OutputFileControllerWrapper(ControllerWrapper):
    def __init__(
        self,
        output_types: typing.List[str],
        default_http_code: HTTPStatus=HTTPStatus.OK,
    ) -> None:
        self.output_types = output_types
        self.default_http_code = default_http_code


class InputPathControllerWrapper(InputControllerWrapper):
    def update_hapic_data(
        self, hapic_data: HapicData,
        processed_data: typing.Any,
    ) -> None:
        hapic_data.path = processed_data

    def get_parameters_data(self, request_parameters: RequestParameters) -> dict:
        return request_parameters.path_parameters


class InputQueryControllerWrapper(InputControllerWrapper):
    def update_hapic_data(
        self, hapic_data: HapicData,
        processed_data: typing.Any,
    ) -> None:
        hapic_data.query = processed_data

    def get_parameters_data(self, request_parameters: RequestParameters) -> dict:
        return request_parameters.query_parameters


class InputBodyControllerWrapper(InputControllerWrapper):
    def update_hapic_data(
        self, hapic_data: HapicData,
        processed_data: typing.Any,
    ) -> None:
        hapic_data.body = processed_data

    def get_parameters_data(self, request_parameters: RequestParameters) -> dict:
        return request_parameters.body_parameters


class InputHeadersControllerWrapper(InputControllerWrapper):
    def update_hapic_data(
        self, hapic_data: HapicData,
        processed_data: typing.Any,
    ) -> None:
        hapic_data.headers = processed_data

    def get_parameters_data(self, request_parameters: RequestParameters) -> dict:
        return request_parameters.header_parameters


class InputFormsControllerWrapper(InputControllerWrapper):
    def update_hapic_data(
        self, hapic_data: HapicData,
        processed_data: typing.Any,
    ) -> None:
        hapic_data.forms = processed_data

    def get_parameters_data(self, request_parameters: RequestParameters) -> dict:
        return request_parameters.form_parameters


class InputFilesControllerWrapper(InputControllerWrapper):
    def update_hapic_data(
        self, hapic_data: HapicData,
        processed_data: typing.Any,
    ) -> None:
        hapic_data.files = processed_data

    def get_parameters_data(self, request_parameters: RequestParameters) -> dict:
        return request_parameters.files_parameters


class ExceptionHandlerControllerWrapper(ControllerWrapper):
    def __init__(
        self,
        handled_exception_class: typing.Type[Exception],
        context: typing.Union[ContextInterface, typing.Callable[[], ContextInterface]],  # nopep8
        schema: marshmallow.Schema,
        http_code: HTTPStatus=HTTPStatus.INTERNAL_SERVER_ERROR,
    ) -> None:
        self.handled_exception_class = handled_exception_class
        self._context = context
        self.http_code = http_code
        self.schema = schema

    @property
    def context(self) -> ContextInterface:
        if callable(self._context):
            return self._context()
        return self._context

    def _execute_wrapped_function(
        self,
        func,
        func_args,
        func_kwargs,
    ) -> typing.Any:
        try:
            return super()._execute_wrapped_function(
                func,
                func_args,
                func_kwargs,
            )
        except self.handled_exception_class as exc:
            # TODO: "error_detail" attribute name should be configurable
            # TODO BS 20171013: use overrideable mechanism, error object given
            #  to schema ? see #15
            raw_response = {
                'message': str(exc),
                'code': None,
                'detail': getattr(exc, 'error_detail', {}),
            }

            error_response = self.context.get_response(
                raw_response,
                self.http_code,
            )
            return error_response
