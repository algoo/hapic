# -*- coding: utf-8 -*-
import json
import typing

from hapic.error import ErrorBuilderInterface

try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus

from hapic.processor import RequestParameters
from hapic.processor import ProcessValidationError

if typing.TYPE_CHECKING:
    from hapic.decorator import DecoratedController


class RouteRepresentation(object):
    def __init__(
        self,
        rule: str,
        method: str,
        original_route_object: typing.Any=None,
    ) -> None:
        self.rule = rule
        self.method = method
        self.original_route_object = original_route_object


class ContextInterface(object):
    def get_request_parameters(self, *args, **kwargs) -> RequestParameters:
        raise NotImplementedError()

    def get_response(
        self,
        # TODO BS 20171228: rename into response_content
        response: str,
        http_code: int,
        mimetype: str='application/json',
    ) -> typing.Any:
        raise NotImplementedError()

    def get_validation_error_response(
        self,
        error: ProcessValidationError,
        http_code: HTTPStatus=HTTPStatus.BAD_REQUEST,
    ) -> typing.Any:
        raise NotImplementedError()

    def find_route(
        self,
        decorated_controller: 'DecoratedController',
    ) -> RouteRepresentation:
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

    def get_default_error_builder(self) -> ErrorBuilderInterface:
        """
        Return a ErrorBuilder who will be used to build default errors
        :return: ErrorBuilderInterface instance
        """
        raise NotImplementedError()

    def add_view(
        self,
        route: str,
        http_method: str,
        view_func: typing.Callable[..., typing.Any],
    ) -> None:
        """
        This method must permit to add a view in current context
        :param route: The route depending of framework format, ex "/foo"
        :param http_method: HTTP method like GET, POST, etc ...
        :param view_func: The view callable
        """
        raise NotImplementedError()

    def serve_directory(
        self,
        route_prefix: str,
        directory_path: str,
    ) -> None:
        """
        Configure a path to serve a directory content
        :param route_prefix: The base url for serve the directory, eg /static
        :param directory_path: The file system path
        """
        raise NotImplementedError()

    def handle_exception(
        self,
        exception_class: typing.Type[Exception],
        http_code: int,
    ) -> None:
        """
        Enable management of this exception during execution of views. If this
        exception caught, an http response will be returned with this http
        code.
        :param exception_class: Exception class to catch
        :param http_code: HTTP code to use in response if exception caught
        """
        raise NotImplementedError()

    def handle_exceptions(
        self,
        exception_classes: typing.List[typing.Type[Exception]],
        http_code: int,
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
    def __init__(
        self,
        exception_class: typing.Type[Exception],
        http_code: int = 500,
    ):
        self.exception_class = exception_class
        self.http_code = http_code


class BaseContext(ContextInterface):
    def get_default_error_builder(self) -> ErrorBuilderInterface:
        """ see hapic.context.ContextInterface#get_default_error_builder"""
        return self.default_error_builder

    def handle_exception(
        self,
        exception_class: typing.Type[Exception],
        http_code: int,
    ) -> None:
        self._add_exception_class_to_catch(exception_class, http_code)

    def handle_exceptions(
        self,
        exception_classes: typing.List[typing.Type[Exception]],
        http_code: int,
    ) -> None:
        for exception_class in exception_classes:
            self._add_exception_class_to_catch(exception_class, http_code)

    def handle_exceptions_decorator_builder(
        self,
        func: typing.Callable[..., typing.Any],
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
                handled_exceptions = reversed(
                    self._get_handled_exception_class_and_http_codes(),
                )
                for handled_exception in handled_exceptions:
                    # TODO BS 2018-05-04: How to be attentive to hierarchy ?
                    if isinstance(exc, handled_exception.exception_class):
                        error_builder = self.get_default_error_builder()
                        error_body = error_builder.build_from_exception(
                            exc,
                            include_traceback=self.is_debug(),
                        )
                        dumped = error_builder.dump(error_body).data
                        return self.get_response(
                            json.dumps(dumped),
                            handled_exception.http_code,
                        )
                raise exc

        return decorator

    def _get_handled_exception_class_and_http_codes(
        self,
    ) -> typing.List[HandledException]:
        """
        :return: A list of tuple where: thirst item of tuple is a exception
        class and second tuple item is a http code. This list will be used by
        `handle_exceptions_decorator_builder` decorator to catch exceptions.
        """
        raise NotImplementedError()

    def _add_exception_class_to_catch(
        self,
        exception_class: typing.Type[Exception],
        http_code: int,
    ) -> None:
        """
        Add an exception class to catch and matching http code. Will be used by
        `handle_exceptions_decorator_builder` decorator to catch exceptions.
        :param exception_class: exception class to catch
        :param http_code: http code to use if this exception catched
        :return:
        """
        raise NotImplementedError()
