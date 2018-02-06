# -*- coding: utf-8 -*-
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


class BaseContext(ContextInterface):
    def get_default_error_builder(self) -> ErrorBuilderInterface:
        """ see hapic.context.ContextInterface#get_default_error_builder"""
        return self.default_error_builder
