# flask regular expression to locate url parameters
from http import HTTPStatus
import json
import re
import typing

from multidict import MultiDict

from hapic.context import BaseContext
from hapic.context import HandledException
from hapic.context import RouteRepresentation
from hapic.decorator import DECORATION_ATTRIBUTE_NAME
from hapic.decorator import DecoratedController
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
from hapic.exception import RouteNotFound
from hapic.processor.main import ProcessValidationError
from hapic.processor.main import RequestParameters

PATH_URL_REGEX = re.compile(r"<([^:<>]+)(?::[^<>]+)?>")


class AgnosticApp(object):
    """
    Framework Agnostic App for AgnosticContext. Cannot
    be run as a true wsgi app.
    """

    def __init__(self):
        self.routes = []  # type: typing.List[RouteRepresentation]

    def route(self, rule: str, method: str, callback: typing.Callable):
        self.routes.append(RouteRepresentation(rule, method, callback))


class AgnosticResponse(object):
    def __init__(self, response, http_code, mimetype):
        self.response = response
        self.http_code = http_code
        self.mimetype = mimetype

    @property
    def status_code(self):
        return self.http_code

    @property
    def body(self):
        return self.response


class AgnosticContext(BaseContext):
    """
    Agnostic Context, doesn't need any web framework.
    This handle:
    - Documentation
    - View-Based-Exception
    This does not handle:
    - Context-Based-Exception
    """

    def __init__(
        self,
        app=AgnosticApp(),
        default_error_builder=MarshmallowDefaultErrorBuilder(),
        path_parameters=None,
        query_parameters=None,
        body_parameters=None,
        form_parameters=None,
        header_parameters=None,
        files_parameters=None,
        debug=False,
        path_url_regex=PATH_URL_REGEX,
    ) -> None:
        super().__init__(default_error_builder=default_error_builder)
        self.debug = debug
        self._handled_exceptions = []  # type: typing.List[HandledException]
        self.app = app
        self._exceptions_handler_installed = False
        self.path_url_regex = path_url_regex
        self.path_parameters = path_parameters or {}
        self.query_parameters = query_parameters or MultiDict()
        self.body_parameters = body_parameters or {}
        self.form_parameters = form_parameters or MultiDict()
        self.header_parameters = header_parameters or {}
        self.files_parameters = files_parameters or {}

    def get_request_parameters(self, *args, **kwargs) -> RequestParameters:
        return RequestParameters(
            path_parameters=self.path_parameters,
            query_parameters=self.query_parameters,
            body_parameters=self.body_parameters,
            form_parameters=self.form_parameters,
            header_parameters=self.header_parameters,
            files_parameters=self.files_parameters,
        )

    def get_validation_error_response(
        self, error: ProcessValidationError, http_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    ) -> typing.Any:
        return self.get_response(
            response=json.dumps(
                {
                    "original_error": {"details": error.details, "message": error.message},
                    "http_code": http_code,
                }
            ),
            http_code=http_code,
        )

    def _add_exception_class_to_catch(
        self, exception_class: typing.Type[Exception], http_code: int
    ) -> None:
        self._handled_exceptions.append(HandledException(exception_class, http_code))

    def _get_handled_exception_class_and_http_codes(self,) -> typing.List[HandledException]:
        return self._handled_exceptions

    def find_route(self, decorated_controller: "DecoratedController"):
        reference = decorated_controller.reference
        for route in self.app.routes:
            route_token = getattr(route.original_route_object, DECORATION_ATTRIBUTE_NAME, None)

            match_with_wrapper = route.original_route_object == reference.wrapper
            match_with_wrapped = route.original_route_object == reference.wrapped
            match_with_token = route_token == reference.token

            if match_with_wrapper or match_with_wrapped or match_with_token:
                return RouteRepresentation(
                    rule=self.get_swagger_path(route.rule),
                    method=route.method.lower(),
                    original_route_object=route,
                )
        # TODO BS 20171010: Raise exception or print error ? see #10
        raise RouteNotFound(
            'Decorated route "{}" was not found in bottle routes'.format(decorated_controller.name)
        )

    def get_swagger_path(self, contextualised_rule: str) -> str:
        return self.path_url_regex.sub(r"{\1}", contextualised_rule)

    def by_pass_output_wrapping(self, response: typing.Any) -> bool:
        if isinstance(response, AgnosticResponse):
            return True
        return False

    def get_response(
        self,
        # TODO BS 20171228: rename into response_content
        response: str,
        http_code: int,
        mimetype: str = "application/json",
    ):
        return AgnosticResponse(response, http_code, mimetype)

    def is_debug(self) -> bool:
        return self.debug
