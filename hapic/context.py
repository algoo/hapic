# -*- coding: utf-8 -*-
import json
import typing

from hapic.data import HapicFile
from hapic.error.main import ErrorBuilderInterface
from hapic.exception import ConfigurationException
from hapic.exception import OutputValidationException
from hapic.exception import ValidationException
from hapic.processor.main import Processor
from hapic.processor.main import ProcessValidationError
from hapic.processor.main import RequestParameters

try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus


if typing.TYPE_CHECKING:
    from hapic.decorator import DecoratedController


class RouteRepresentation(object):
    def __init__(self, rule: str, method: str, original_route_object: typing.Any = None) -> None:
        self.rule = rule
        self.method = method
        self.original_route_object = original_route_object


class ContextInterface(object):
    def get_request_parameters(self, *args, **kwargs) -> RequestParameters:
        raise NotImplementedError()

    def set_processor_class(self, processor_class: typing.Type[Processor]) -> None:
        """
        Set processor class to be used in the context. Processor class
        will be used to validate and generate errors.
        It will be used to validate error, eg.
        in BaseContext.handle_exceptions_decorator_builder.
        :param processor_class: Processor subclass
        """
        raise NotImplementedError()

    def get_response(
        self,
        # TODO BS 20171228: rename into response_content
        response: str,
        http_code: int,
        mimetype: str = "application/json",
    ) -> typing.Any:
        raise NotImplementedError()

    def get_file_response(self, file_response: HapicFile, http_code: int) -> typing.Any:
        raise NotImplementedError()

    def get_validation_error_response(
        self, error: ProcessValidationError, http_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    ) -> typing.Any:
        raise NotImplementedError()

    def find_route(self, decorated_controller: "DecoratedController") -> RouteRepresentation:
        raise NotImplementedError()

    # TODO BS 20171228: rename into openapi !
    def get_swagger_path(self, contextualised_rule: str) -> str:
        """
        Return OpenAPI path with context path
        TODO BS 20171228: Give example
        :param contextualised_rule: path of original context
        :return: OpenAPI path
        """
        raise NotImplementedError()

    # TODO BS 20171228: rename into "bypass"
    def by_pass_output_wrapping(self, response: typing.Any) -> bool:
        """
        Return True if the controller response is the final response object:
        we do not have to apply any processing on it.
        :param response: the original response of controller
        :return:
        """
        raise NotImplementedError()

    @property
    def default_error_builder(self) -> ErrorBuilderInterface:
        """
        Return a ErrorBuilder who will be used to build default errors
        Raise ConfigurationException if no default_error_builder
        :return: ErrorBuilderInterface instance
        """
        raise NotImplementedError()

    @default_error_builder.setter
    def default_error_builder(self, error_builder: ErrorBuilderInterface) -> None:
        """
        Set the default error builder for this context
        :param error_builder: ErrorBuilderInterface instance to use as
            default error builder
        """
        raise NotImplementedError()

    def add_view(
        self, route: str, http_method: str, view_func: typing.Callable[..., typing.Any]
    ) -> None:
        """
        This method must permit to add a view in current context
        :param route: The route depending of framework format, ex "/foo"
        :param http_method: HTTP method like GET, POST, etc ...
        :param view_func: The view callable
        """
        raise NotImplementedError()

    def serve_directory(self, route_prefix: str, directory_path: str) -> None:
        """
        Configure a path to serve a directory content
        :param route_prefix: The base url for serve the directory, eg /static
        :param directory_path: The file system path
        """
        raise NotImplementedError()

    def handle_exception(self, exception_class: typing.Type[Exception], http_code: int) -> None:
        """
        Enable management of this exception during execution of views. If this
        exception caught, an http response will be returned with this http
        code.
        :param exception_class: Exception class to catch
        :param http_code: HTTP code to use in response if exception caught
        """
        raise NotImplementedError()

    def handle_exceptions(
        self, exception_classes: typing.List[typing.Type[Exception]], http_code: int
    ) -> None:
        """
        Enable management of these exceptions during execution of views. If
        this exception caught, an http response will be returned with this http
        code.
        :param exception_classes: Exception classes to catch
        :param http_code: HTTP code to use in response if exception caught
        """
        raise NotImplementedError()

    def is_debug(self) -> bool:
        """
        Method called to know if Hapic has been called in debug mode.
        Debug mode provide some informations like debug trace and error
        message in body when internal error happen.
        :return: True if in debug mode
        """
        raise NotImplementedError()


class HandledException(object):
    """
    Representation of an handled exception with it's http code
    """

    def __init__(self, exception_class: typing.Type[Exception], http_code: int = 500):
        self.exception_class = exception_class
        self.http_code = http_code


class BaseContext(ContextInterface):
    def __init__(
        self,
        processor_class: typing.Optional[typing.Type[Processor]] = None,
        default_error_builder: ErrorBuilderInterface = None,
    ) -> None:
        """
        Set processor_class of the context. It will be used to validate
        hapic generated errors. This parameter is not designed to be used by
        end user. Hapic automatically set it thought
        `hapic.context.BaseContext#set_processor_class` in
        `hapic.hapic.Hapic#set_context`.
        :param processor_class: Processor class
        """
        self._processor_class = processor_class
        self._default_error_builder = default_error_builder

    @property
    def default_error_builder(self) -> ErrorBuilderInterface:
        """ see hapic.context.ContextInterface#get_default_error_builder"""
        if self._default_error_builder is None:
            raise ConfigurationException("No default_error_builder given")

        return self._default_error_builder

    @default_error_builder.setter
    def default_error_builder(self, error_builder: ErrorBuilderInterface) -> None:
        """
        see hapic.context.ContextInterface#set_default_error_builder
        """
        self._default_error_builder = error_builder

    def set_processor_class(self, processor_class: typing.Type[Processor]) -> None:
        """
        Change processor class associated to this context. It will be used
        to validate error, eg. in handle_exceptions_decorator_builder.
        :param processor_class: Processor subclass
        """
        self._processor_class = processor_class

    def handle_exception(self, exception_class: typing.Type[Exception], http_code: int) -> None:
        self._add_exception_class_to_catch(exception_class, http_code)

    def handle_exceptions(
        self, exception_classes: typing.List[typing.Type[Exception]], http_code: int
    ) -> None:
        for exception_class in exception_classes:
            self._add_exception_class_to_catch(exception_class, http_code)

    def _get_dumped_error_from_exception_error(self, exception: Exception) -> typing.Any:
        """
        Build dumped error from given exception.
        Raise OutputValidationException if error built from error_builder is
        not valid.
        :param exception: exception to use to build error
        :return: dumped error object
        """
        error_builder = self.default_error_builder
        error_body = error_builder.build_from_exception(
            exception, include_traceback=self.is_debug()
        )
        processor = self._processor_class(error_builder.get_schema())

        try:
            return processor.dump(error_body)
        except ValidationException as exc:
            raise OutputValidationException(
                "Validation error of error response: {}".format(str(exc))
            ) from exc

    def _get_dumped_error_from_validation_error(self, error: ProcessValidationError) -> typing.Any:
        """
        Build dumped error from given validation error.
        Raise OutputValidationException if error built from error_builder is
        not valid.
        :param error: ProcessValidationError instance
        :return: dumped error object
        """
        error_builder = self.default_error_builder
        error_content = error_builder.build_from_validation_error(error)
        processor = self._processor_class(error_builder.get_schema())

        try:
            return processor.dump(error_content)
        except ValidationException as exc:
            raise OutputValidationException(
                "Validation error of error response: {}".format(str(exc))
            ) from exc

    def handle_exceptions_decorator_builder(
        self, func: typing.Callable[..., typing.Any]
    ) -> typing.Callable[..., typing.Any]:
        """
        Return a decorator who catch exceptions raised during given function
        execution and return a response built by the default error builder.

        :param func: decorated function
        :return: the decorator
        """

        def decorator(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                # Reverse list to read first user given exception before
                # the hapic default Exception catch
                handled_exceptions = reversed(self._get_handled_exception_class_and_http_codes())
                # TODO BS 2018-05-04: How to be attentive to hierarchy ?
                for handled_exception in handled_exceptions:
                    if isinstance(exc, handled_exception.exception_class):
                        dumped_error = self._get_dumped_error_from_exception_error(exc)
                        return self.get_response(
                            json.dumps(dumped_error), handled_exception.http_code
                        )
                raise exc

        return decorator

    def _get_handled_exception_class_and_http_codes(self,) -> typing.List[HandledException]:
        """
        :return: A list of tuple where: thirst item of tuple is a exception
        class and second tuple item is a http code. This list will be used by
        `handle_exceptions_decorator_builder` decorator to catch exceptions.
        """
        raise NotImplementedError()

    def _add_exception_class_to_catch(
        self, exception_class: typing.Type[Exception], http_code: int
    ) -> None:
        """
        Add an exception class to catch and matching http code. Will be used by
        `handle_exceptions_decorator_builder` decorator to catch exceptions.
        :param exception_class: exception class to catch
        :param http_code: http code to use if this exception catched
        :return:
        """
        raise NotImplementedError()
