# -*- coding: utf-8 -*-
import functools
import json
import logging
import traceback
import typing

from multidict import MultiDict

from hapic.context import ContextInterface
from hapic.data import HapicData
from hapic.description import ControllerDescription
from hapic.error.main import ErrorBuilderInterface
from hapic.exception import OutputValidationException
from hapic.exception import ProcessException
from hapic.exception import ValidationException
from hapic.processor.main import Processor
from hapic.processor.main import ProcessValidationError
from hapic.processor.main import RequestParameters
from hapic.type import TYPE_SCHEMA
from hapic.util import LOGGER_NAME

try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus


# TODO: Ensure usage of DECORATION_ATTRIBUTE_NAME is documented and
# var names correctly choose.  see #6
DECORATION_ATTRIBUTE_NAME = "_hapic_decoration_token"


class ControllerReference(object):
    def __init__(self, wrapper: typing.Callable, wrapped: typing.Callable, token: str) -> None:
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

    def get_doc_string(self) -> str:
        if self.wrapper.__doc__:
            return self.wrapper.__doc__.strip()

        if self.wrapped.__doc__:
            return self.wrapper.__doc__.strip()

        return ""


class ControllerWrapper(object):
    def __init__(
        self,
        context: typing.Union[ContextInterface, typing.Callable[[], ContextInterface]],
        processor_factory: typing.Callable[[typing.Optional[TYPE_SCHEMA]], Processor],
        error_http_code: HTTPStatus = HTTPStatus.BAD_REQUEST,
        default_http_code: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        """
        ControllerWrapper are the view wrapper. It's job is to intercept
        input and output to run hapic controls.
        :param context: context to use with this wrapper
        :param processor_factory: callable to build processor
        :param error_http_code: http code to use in case of error
        :param default_http_code: http code to use in case of success
        """
        self._context = context
        self._processor_factory = processor_factory
        self._processor = None  # type: Processor
        self.error_http_code = error_http_code
        self.default_http_code = default_http_code

    @property
    def context(self) -> ContextInterface:
        """
        Wrapper associated context. It return context given when
        wrapper used or default hapic context.
        :return: ContextInterface object
        """
        if callable(self._context):
            return self._context()
        return self._context

    @property
    def processor(self) -> Processor:
        """
        Wrapper associated processor. It return processor given when
        wrapper used or default hapic processor.
        :return: Processor object
        """
        if self._processor is None:
            self._processor = self._processor_factory()

        return self._processor

    def before_wrapped_func(
        self, func_args: typing.Tuple[typing.Any, ...], func_kwargs: typing.Dict[str, typing.Any]
    ) -> typing.Union[None, typing.Any]:
        pass

    def after_wrapped_function(self, response: typing.Any) -> typing.Any:
        return response

    def get_wrapper(self, func: "typing.Callable") -> "typing.Callable":
        # async def wrapper(*args, **kwargs) -> typing.Any:
        def wrapper(*args, **kwargs) -> typing.Any:
            # Note: Design of before_wrapped_func can be to update kwargs
            # by reference here
            replacement_response = self.before_wrapped_func(args, kwargs)
            if replacement_response is not None:
                return replacement_response

            response = self._execute_wrapped_function(func, args, kwargs)
            new_response = self.after_wrapped_function(response)
            return new_response

        return functools.update_wrapper(wrapper, func)

    def _execute_wrapped_function(self, func, func_args, func_kwargs) -> typing.Any:
        return func(*func_args, **func_kwargs)


class InputOutputControllerWrapper(ControllerWrapper):
    pass


class InputControllerWrapper(InputOutputControllerWrapper):
    def before_wrapped_func(
        self, func_args: typing.Tuple[typing.Any, ...], func_kwargs: typing.Dict[str, typing.Any]
    ) -> typing.Any:
        # Retrieve hapic_data instance or create new one
        # hapic_data is given though decorators
        # Important note here: func_kwargs is update by reference !
        hapic_data = self.ensure_hapic_data(func_kwargs)
        request_parameters = self.get_request_parameters(func_args, func_kwargs)

        try:
            processed_data = self.get_processed_data(request_parameters)
            self.update_hapic_data(hapic_data, processed_data)
        except ProcessException:
            error_response = self.get_error_response(request_parameters)
            return error_response

    @classmethod
    def ensure_hapic_data(cls, func_kwargs: typing.Dict[str, typing.Any]) -> HapicData:
        # TODO: Permit other name than "hapic_data" ? see #7
        try:
            return func_kwargs["hapic_data"]
        except KeyError:
            hapic_data = HapicData()
            func_kwargs["hapic_data"] = hapic_data
            return hapic_data

    def get_request_parameters(
        self, func_args: typing.Tuple[typing.Any, ...], func_kwargs: typing.Dict[str, typing.Any]
    ) -> RequestParameters:
        return self.context.get_request_parameters(*func_args, **func_kwargs)

    def get_processed_data(self, request_parameters: RequestParameters) -> typing.Any:
        parameters_data = self.get_parameters_data(request_parameters)
        processed_data = self.processor.load(parameters_data)
        return processed_data

    def get_parameters_data(self, request_parameters: RequestParameters) -> dict:
        raise NotImplementedError()

    def update_hapic_data(
        self, hapic_data: HapicData, processed_data: typing.Dict[str, typing.Any]
    ) -> None:
        raise NotImplementedError()

    def get_error_response(self, request_parameters: RequestParameters) -> typing.Any:
        parameters_data = self.get_parameters_data(request_parameters)
        error = self._get_processor_error(parameters_data)
        error_response = self.context.get_validation_error_response(
            error, http_code=self.error_http_code
        )
        return error_response

    def _get_processor_error(self, parameters_data: typing.Any) -> ProcessValidationError:
        return self.processor.get_input_validation_error(parameters_data)


# TODO BS 2018-07-23: This class is an async version of InputControllerWrapper
# (and ControllerWrapper.get_wrapper rewrite) to permit async compatibility.
# Please re-think about code refact. TAG: REFACT_ASYNC
class AsyncInputControllerWrapper(InputControllerWrapper):
    def get_wrapper(self, func: "typing.Callable") -> "typing.Callable":
        async def wrapper(*args, **kwargs) -> typing.Any:
            # Note: Design of before_wrapped_func can be to update kwargs
            # by reference here
            replacement_response = await self.before_wrapped_func(args, kwargs)
            if replacement_response is not None:
                return replacement_response

            response = await self._execute_wrapped_function(func, args, kwargs)
            new_response = self.after_wrapped_function(response)
            return new_response

        return functools.update_wrapper(wrapper, func)

    async def before_wrapped_func(
        self, func_args: typing.Tuple[typing.Any, ...], func_kwargs: typing.Dict[str, typing.Any]
    ) -> typing.Any:
        # Retrieve hapic_data instance or create new one
        # hapic_data is given though decorators
        # Important note here: func_kwargs is update by reference !
        hapic_data = self.ensure_hapic_data(func_kwargs)
        request_parameters = self.get_request_parameters(func_args, func_kwargs)

        try:
            processed_data = await self.get_processed_data(request_parameters)
            self.update_hapic_data(hapic_data, processed_data)
        except ProcessException:
            error_response = await self.get_error_response(request_parameters)
            return error_response

    async def get_processed_data(self, request_parameters: RequestParameters) -> typing.Any:
        parameters_data = await self.get_parameters_data(request_parameters)
        processed_data = self.processor.load(parameters_data)
        return processed_data


class OutputControllerWrapper(InputOutputControllerWrapper):
    def __init__(
        self,
        context: typing.Union[ContextInterface, typing.Callable[[], ContextInterface]],
        processor_factory: typing.Callable[[typing.Optional[TYPE_SCHEMA]], Processor],
        error_http_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR,
        default_http_code: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        super().__init__(context, processor_factory, error_http_code, default_http_code)

    def get_error_response(self, response: typing.Any) -> typing.Any:
        error = self.processor.get_output_validation_error(response)
        error_response = self.context.get_validation_error_response(
            error, http_code=self.error_http_code
        )
        return error_response

    def after_wrapped_function(self, response: typing.Any) -> typing.Any:
        try:
            if self.context.by_pass_output_wrapping(response):
                return response

            processed_response = self.processor.dump(response)
            prepared_response = self.context.get_response(
                json.dumps(processed_response), self.default_http_code
            )
            return prepared_response
        except ProcessException:
            # TODO: ici ou ailleurs: il faut pas forcement donner le detail
            # de l'erreur (mode debug par exemple)  see #8
            error_response = self.get_error_response(response)
            return error_response


class DecoratedController(object):
    def __init__(
        self, reference: ControllerReference, description: ControllerDescription, name: str = ""
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


# TODO BS 2018-07-23: This class is an async version of
# OutputBodyControllerWrapper (ControllerWrapper.get_wrapper rewrite)
# to permit async compatibility.
# Please re-think about code refact. TAG: REFACT_ASYNC
class AsyncOutputBodyControllerWrapper(OutputControllerWrapper):
    def get_wrapper(self, func: "typing.Callable") -> "typing.Callable":
        # async def wrapper(*args, **kwargs) -> typing.Any:
        async def wrapper(*args, **kwargs) -> typing.Any:
            # Note: Design of before_wrapped_func can be to update kwargs
            # by reference here
            replacement_response = self.before_wrapped_func(args, kwargs)
            if replacement_response is not None:
                return replacement_response

            response = await self._execute_wrapped_function(func, args, kwargs)
            new_response = self.after_wrapped_function(response)
            return new_response

        return functools.update_wrapper(wrapper, func)


class AsyncOutputStreamControllerWrapper(OutputControllerWrapper):
    """
    This controller wrapper produce a wrapper who caught the http view items
    to check and serialize them into a stream response.
    """

    def __init__(
        self,
        context: typing.Union[ContextInterface, typing.Callable[[], ContextInterface]],
        processor_factory: typing.Callable[[typing.Optional[TYPE_SCHEMA]], Processor],
        error_http_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR,
        default_http_code: HTTPStatus = HTTPStatus.OK,
        ignore_on_error: bool = True,
    ) -> None:
        super().__init__(context, processor_factory, error_http_code, default_http_code)
        self.ignore_on_error = ignore_on_error

    def get_wrapper(self, func: "typing.Callable") -> "typing.Callable":
        # async def wrapper(*args, **kwargs) -> typing.Any:
        async def wrapper(*args, **kwargs) -> typing.Any:
            # Note: Design of before_wrapped_func can be to update kwargs
            # by reference here
            replacement_response = self.before_wrapped_func(args, kwargs)
            if replacement_response is not None:
                return replacement_response

            stream_response = await self.context.get_stream_response_object(args, kwargs)

            response_object = self._execute_wrapped_function(func, args, kwargs)

            # To be compatible with python3.5 and python3.7, we must inspect
            # the object. If it is an async_generator, nothing to do. Else,
            # we must await it.
            # To see example, in python3.5:
            #    tests.ext.unit.test_aiohttp.TestAiohttpExt#test_aiohttp_output_stream__ok__nominal_case
            # In python 3.6+:
            #    tests.ext.unit.test_aiohttp.TestAiohttpExt#test_aiohttp_output_stream__ok__py37
            # TODO BS 2018-11-19: A cleaner way to test if it is an
            # async_generator object ?
            if type(response_object).__name__ == "async_generator":
                iterable_response_object = response_object
            else:
                iterable_response_object = await response_object

            async for stream_item in iterable_response_object:
                try:
                    serialized_item = self._get_serialized_item(stream_item)
                    await self.context.feed_stream_response(stream_response, serialized_item)
                except ValidationException:
                    if not self.ignore_on_error:
                        # TODO BS 2018-07-31: Something should inform about
                        # error, a log ?
                        return stream_response

            return stream_response

        return functools.update_wrapper(wrapper, func)

    def _get_serialized_item(self, item_object: typing.Any) -> dict:
        return self.processor.dump(item_object)


class OutputHeadersControllerWrapper(OutputControllerWrapper):
    pass


class OutputFileControllerWrapper(OutputControllerWrapper):
    def __init__(
        self,
        context: typing.Union[ContextInterface, typing.Callable[[], ContextInterface]],
        processor_factory: typing.Callable[[typing.Optional[TYPE_SCHEMA]], Processor],
        output_types: typing.List[str],
        error_http_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR,
        default_http_code: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        super().__init__(context, processor_factory, error_http_code, default_http_code)
        self.output_types = output_types

    def after_wrapped_function(self, response: typing.Any) -> typing.Any:
        try:
            if self.context.by_pass_output_wrapping(response):
                return response

            processed_response = self.processor.dump_output_file(response)
            prepared_response = self.context.get_file_response(
                processed_response, self.default_http_code
            )
            return prepared_response
        except ProcessException:
            # TODO: ici ou ailleurs: il faut pas forcement donner le detail
            # de l'erreur (mode debug par exemple)  see #8
            error_response = self.get_error_response(response)
            return error_response


# TODO GM 2019-03-26: This class is an async version of
# OutputFileControllerWrapper (ControllerWrapper.get_wrapper rewrite)
# to permit async compatibility.
# Please re-think about code refact. TAG: REFACT_ASYNC
class AsyncOutputFileControllerWrapper(OutputFileControllerWrapper):
    def get_wrapper(self, func: "typing.Callable") -> "typing.Callable":
        # async def wrapper(*args, **kwargs) -> typing.Any:
        async def wrapper(*args, **kwargs) -> typing.Any:
            # Note: Design of before_wrapped_func can be to update kwargs
            # by reference here
            replacement_response = self.before_wrapped_func(args, kwargs)
            if replacement_response is not None:
                return replacement_response

            response = await self._execute_wrapped_function(func, args, kwargs)
            new_response = self.after_wrapped_function(response)
            return new_response

        return functools.update_wrapper(wrapper, func)


class InputPathControllerWrapper(InputControllerWrapper):
    def update_hapic_data(self, hapic_data: HapicData, processed_data: typing.Any) -> None:
        hapic_data.path = processed_data

    def get_parameters_data(self, request_parameters: RequestParameters) -> dict:
        return request_parameters.path_parameters


# TODO BS 2018-07-23: This class is an async version of
#  InputPathControllerWrapper to permit async compatibility. Please re-think
#  about code refact
#  TAG: REFACT_ASYNC
class AsyncInputPathControllerWrapper(InputPathControllerWrapper):
    def get_wrapper(self, func: "typing.Callable") -> "typing.Callable":
        # async def wrapper(*args, **kwargs) -> typing.Any:
        async def wrapper(*args, **kwargs) -> typing.Any:
            # Note: Design of before_wrapped_func can be to update kwargs
            # by reference here
            replacement_response = self.before_wrapped_func(args, kwargs)
            if replacement_response is not None:
                return replacement_response

            response = await self._execute_wrapped_function(func, args, kwargs)
            new_response = self.after_wrapped_function(response)
            return new_response

        return functools.update_wrapper(wrapper, func)

    async def _execute_wrapped_function(self, func, func_args, func_kwargs) -> typing.Any:
        return await func(*func_args, **func_kwargs)


class InputQueryControllerWrapper(InputControllerWrapper):
    def __init__(
        self,
        context: typing.Union[ContextInterface, typing.Callable[[], ContextInterface]],
        processor_factory: typing.Callable[[typing.Optional[TYPE_SCHEMA]], Processor],
        error_http_code: HTTPStatus = HTTPStatus.BAD_REQUEST,
        default_http_code: HTTPStatus = HTTPStatus.OK,
        as_list: typing.List[str] = None,
    ) -> None:
        super().__init__(context, processor_factory, error_http_code, default_http_code)
        self.as_list = as_list or []  # FDV

    def update_hapic_data(self, hapic_data: HapicData, processed_data: typing.Any) -> None:
        hapic_data.query = processed_data

    def get_parameters_data(self, request_parameters: RequestParameters) -> MultiDict:
        # Parameters are updated considering eventual as_list parameters
        if self.as_list:
            query_parameters = MultiDict()
            for parameter_name in request_parameters.query_parameters.keys():
                if parameter_name in query_parameters:
                    continue

                if parameter_name in self.as_list:
                    query_parameters[parameter_name] = request_parameters.query_parameters.getall(
                        parameter_name
                    )
                else:
                    query_parameters[parameter_name] = request_parameters.query_parameters.get(
                        parameter_name
                    )
            return query_parameters

        return request_parameters.query_parameters


# TODO BS 2018-07-23: This class is an async version of
#  InputQueryControllerWrapper to permit async compatibility. Please re-think
#  about code refact
# TAG: REFACT_ASYNC
class AsyncInputQueryControllerWrapper(InputQueryControllerWrapper):
    def get_wrapper(self, func: "typing.Callable") -> "typing.Callable":
        # async def wrapper(*args, **kwargs) -> typing.Any:
        async def wrapper(*args, **kwargs) -> typing.Any:
            # Note: Design of before_wrapped_func can be to update kwargs
            # by reference here
            replacement_response = self.before_wrapped_func(args, kwargs)
            if replacement_response is not None:
                return replacement_response

            response = await self._execute_wrapped_function(func, args, kwargs)
            new_response = self.after_wrapped_function(response)
            return new_response

        return functools.update_wrapper(wrapper, func)

    async def _execute_wrapped_function(self, func, func_args, func_kwargs) -> typing.Any:
        return await func(*func_args, **func_kwargs)


class InputBodyControllerWrapper(InputControllerWrapper):
    def update_hapic_data(self, hapic_data: HapicData, processed_data: typing.Any) -> None:
        hapic_data.body = processed_data

    def get_parameters_data(self, request_parameters: RequestParameters) -> dict:
        return request_parameters.body_parameters


# TODO BS 2018-07-23: This class is an async version of InputControllerWrapper
# to permit async compatibility. Please re-think about code refact
# TAG: REFACT_ASYNC
class AsyncInputBodyControllerWrapper(AsyncInputControllerWrapper):
    def update_hapic_data(self, hapic_data: HapicData, processed_data: typing.Any) -> None:
        hapic_data.body = processed_data

    async def get_parameters_data(self, request_parameters: RequestParameters) -> dict:
        return await request_parameters.body_parameters

    async def get_error_response(self, request_parameters: RequestParameters) -> typing.Any:
        parameters_data = await self.get_parameters_data(request_parameters)
        error = self.processor.get_input_validation_error(parameters_data)
        error_response = self.context.get_validation_error_response(
            error, http_code=self.error_http_code
        )
        return error_response


class InputHeadersControllerWrapper(InputControllerWrapper):
    def update_hapic_data(self, hapic_data: HapicData, processed_data: typing.Any) -> None:
        hapic_data.headers = processed_data

    def get_parameters_data(self, request_parameters: RequestParameters) -> dict:
        return request_parameters.header_parameters


class InputFormsControllerWrapper(InputControllerWrapper):
    def update_hapic_data(self, hapic_data: HapicData, processed_data: typing.Any) -> None:
        hapic_data.forms = processed_data

    def get_parameters_data(self, request_parameters: RequestParameters) -> dict:
        return request_parameters.form_parameters


class InputFilesControllerWrapper(InputControllerWrapper):
    def update_hapic_data(self, hapic_data: HapicData, processed_data: typing.Any) -> None:
        hapic_data.files = processed_data

    def get_processed_data(self, request_parameters: RequestParameters) -> typing.Any:
        parameters_data = self.get_parameters_data(request_parameters)
        processed_data = self.processor.load_files_input(parameters_data)
        return processed_data

    def get_parameters_data(self, request_parameters: RequestParameters) -> dict:
        return request_parameters.files_parameters

    def _get_processor_error(self, parameters_data: typing.Any) -> ProcessValidationError:
        return self.processor.get_input_files_validation_error(parameters_data)


# TODO BS 2019-01-11: This class is an async version of
# InputFilesControllerWrapper to permit async compatibility.
# Please re-think about code refact
# TAG: REFACT_ASYNC
class AsyncInputFilesControllerWrapper(AsyncInputControllerWrapper):
    def update_hapic_data(self, hapic_data: HapicData, processed_data: typing.Any) -> None:
        hapic_data.files = processed_data

    async def get_processed_data(self, request_parameters: RequestParameters) -> typing.Any:
        parameters_data = await self.get_parameters_data(request_parameters)
        processed_data = self.processor.load_files_input(parameters_data)
        return processed_data

    async def get_parameters_data(self, request_parameters: RequestParameters) -> dict:
        return await request_parameters.files_parameters

    def _get_processor_error(self, parameters_data: typing.Any) -> ProcessValidationError:
        return self.processor.get_input_files_validation_error(parameters_data)

    async def get_error_response(self, request_parameters: RequestParameters) -> typing.Any:
        parameters_data = await self.get_parameters_data(request_parameters)
        error = self._get_processor_error(parameters_data)
        error_response = self.context.get_validation_error_response(
            error, http_code=self.error_http_code
        )
        return error_response


class ExceptionHandlerControllerWrapper(ControllerWrapper):
    """
    This wrapper is used to wrap a controller and catch given exception if
    raised. An error will be generated in collaboration with context and
    returned.
    """

    def __init__(
        self,
        handled_exception_class: typing.Type[Exception],
        context: typing.Union[ContextInterface, typing.Callable[[], ContextInterface]],
        error_builder: typing.Union[
            ErrorBuilderInterface, typing.Callable[[], ErrorBuilderInterface]
        ],
        processor_factory: typing.Callable[[typing.Optional[TYPE_SCHEMA]], Processor],
        http_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR,
        description: str = None,
    ) -> None:
        super().__init__(context, processor_factory, error_http_code=http_code)
        self.handled_exception_class = handled_exception_class
        self._context = context
        # TODO - G.M - 2018-11-30 - Deal better with int/HTTPStatus conversion
        if isinstance(http_code, HTTPStatus):
            default_description = "{}: {}".format(http_code.name, http_code.description)
        else:
            default_description = str(int(http_code))
        self.description = (
            description or self.handled_exception_class.__doc__ or default_description
        )  # DFV
        self._error_builder = error_builder

    @property
    def context(self) -> ContextInterface:
        if callable(self._context):
            return self._context()
        return self._context

    @property
    def error_builder(self) -> ErrorBuilderInterface:
        if callable(self._error_builder):
            return self._error_builder()
        return self._error_builder

    def _execute_wrapped_function(self, func, func_args, func_kwargs) -> typing.Any:
        try:
            return super()._execute_wrapped_function(func, func_args, func_kwargs)
        except self.handled_exception_class as exc:
            return self._build_error_response(exc)

    def _build_error_response(self, exc: Exception) -> typing.Any:
        response_content = self.error_builder.build_from_exception(
            exc, include_traceback=self.context.is_debug()
        )
        processor = self._processor_factory(self.error_builder.get_schema())
        # Check error format
        try:
            dumped = processor.dump(response_content)
        except ValidationException as exc:
            raise OutputValidationException(
                "Validation error during dump " "of error response: {}".format(str(exc))
            ) from exc

        error_response = self.context.get_response(json.dumps(dumped), self.error_http_code)
        self._logger = logging.getLogger(LOGGER_NAME)
        self._logger.info(
            "Exception {exc} occured, return "
            "{http_code} http_code : {msg}".format(
                exc=type(exc).__name__, http_code=self.error_http_code, msg=str(exc)
            )
        )
        # NOTE BS 2018-09-28: log on debug because it is an http framework error,
        # managed and dumped in response. Not an hapic error.
        self._logger.debug(traceback.format_exc())
        return error_response


# TODO BS 2018-07-23: This class is an async version of
# ExceptionHandlerControllerWrapper
# to permit async compatibility. Please re-think about code refact
# TAG: REFACT_ASYNC
class AsyncExceptionHandlerControllerWrapper(ExceptionHandlerControllerWrapper):
    def get_wrapper(self, func: "typing.Callable") -> "typing.Callable":
        # async def wrapper(*args, **kwargs) -> typing.Any:
        async def wrapper(*args, **kwargs) -> typing.Any:
            # Note: Design of before_wrapped_func can be to update kwargs
            # by reference here
            replacement_response = self.before_wrapped_func(args, kwargs)
            if replacement_response is not None:
                return replacement_response

            response = await self._execute_wrapped_function(func, args, kwargs)
            new_response = self.after_wrapped_function(response)
            return new_response

        return functools.update_wrapper(wrapper, func)

    async def _execute_wrapped_function(self, func, func_args, func_kwargs) -> typing.Any:
        try:
            return await func(*func_args, **func_kwargs)
        except self.handled_exception_class as exc:
            return self._build_error_response(exc)
