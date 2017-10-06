# -*- coding: utf-8 -*-
import functools
import typing
from http import HTTPStatus

from hapic.data import HapicData
from hapic.description import ControllerDescription
from hapic.exception import ProcessException
from hapic.context import ContextInterface
from hapic.processor import ProcessorInterface
from hapic.processor import RequestParameters


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
        context: ContextInterface,
        processor: ProcessorInterface,
        error_http_code: HTTPStatus=HTTPStatus.BAD_REQUEST,
        default_http_code: HTTPStatus=HTTPStatus.OK,
    ) -> None:
        self.context = context
        self.processor = processor
        self.error_http_code = error_http_code
        self.default_http_code = default_http_code


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
        # TODO: Permit other name than "hapic_data" ?
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
        error = self.processor.get_validation_error(
            request_parameters.body_parameters,
        )
        error_response = self.context.get_validation_error_response(
            error,
            http_code=self.error_http_code,
        )
        return error_response


class OutputControllerWrapper(InputOutputControllerWrapper):
    def __init__(
        self,
        context: ContextInterface,
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
            processed_response = self.processor.process(response)
            prepared_response = self.context.get_response(
                processed_response,
                self.default_http_code,
            )
            return prepared_response
        except ProcessException:
            # TODO: ici ou ailleurs: il faut pas forcement donner le detail
            # de l'erreur (mode debug par exemple)
            error_response = self.get_error_response(response)
            return error_response


class DecoratedController(object):
    def __init__(
        self,
        reference: 'typing.Callable[..., typing.Any]',
        description: ControllerDescription,
    ) -> None:
        self._reference = reference
        self._description = description

    @property
    def reference(self) -> 'typing.Callable[..., typing.Any]':
        return self._reference

    @property
    def description(self) -> ControllerDescription:
        return self._description


class OutputBodyControllerWrapper(OutputControllerWrapper):
    pass


class OutputHeadersControllerWrapper(OutputControllerWrapper):
    # TODO: write me
    pass


class InputPathControllerWrapper(InputControllerWrapper):
    def update_hapic_data(
        self, hapic_data: HapicData,
        processed_data: typing.Any,
    ) -> None:
        hapic_data.path = processed_data

    def get_processed_data(
        self,
        request_parameters: RequestParameters,
    ) -> typing.Any:
        processed_data = self.processor.process(
            request_parameters.path_parameters,
        )
        return processed_data


class InputQueryControllerWrapper(InputControllerWrapper):
    def update_hapic_data(
        self, hapic_data: HapicData,
        processed_data: typing.Any,
    ) -> None:
        hapic_data.query = processed_data

    def get_processed_data(
        self,
        request_parameters: RequestParameters,
    ) -> typing.Any:
        processed_data = self.processor.process(
            request_parameters.query_parameters,
        )
        return processed_data


class InputBodyControllerWrapper(InputControllerWrapper):
    def update_hapic_data(
        self, hapic_data: HapicData,
        processed_data: typing.Any,
    ) -> None:
        hapic_data.body = processed_data

    def get_processed_data(
        self,
        request_parameters: RequestParameters,
    ) -> typing.Any:
        processed_data = self.processor.process(
            request_parameters.body_parameters,
        )
        return processed_data


class InputHeadersControllerWrapper(InputControllerWrapper):
    def update_hapic_data(
        self, hapic_data: HapicData,
        processed_data: typing.Any,
    ) -> None:
        hapic_data.headers = processed_data

    def get_processed_data(
        self,
        request_parameters: RequestParameters,
    ) -> typing.Any:
        processed_data = self.processor.process(
            request_parameters.header_parameters,
        )
        return processed_data


class InputFormsControllerWrapper(InputControllerWrapper):
    def update_hapic_data(
        self, hapic_data: HapicData,
        processed_data: typing.Any,
    ) -> None:
        hapic_data.forms = processed_data

    def get_processed_data(
        self,
        request_parameters: RequestParameters,
    ) -> typing.Any:
        processed_data = self.processor.process(
            request_parameters.form_parameters,
        )
        return processed_data


class ExceptionHandlerControllerWrapper(ControllerWrapper):
    def __init__(
        self,
        handled_exception_class: typing.Type[Exception],
        context: ContextInterface,
        http_code: HTTPStatus=HTTPStatus.INTERNAL_SERVER_ERROR,
    ) -> None:
        self.handled_exception_class = handled_exception_class
        self.context = context
        self.http_code = http_code

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
            # TODO: error_dict configurable name
            # TODO: Who assume error structure ? We have to rethink it
            error_dict = {
                'error_message': str(exc),
            }
            if hasattr(exc, 'error_dict'):
                error_dict.update(exc.error_dict)

            error_response = self.context.get_response(
                error_dict,
                self.http_code,
            )
            return error_response
