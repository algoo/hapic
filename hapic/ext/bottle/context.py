# -*- coding: utf-8 -*-
import json
import re
import typing

import bottle
from multidict import MultiDict

from hapic.context import BaseContext
from hapic.context import HandledException
from hapic.context import RouteRepresentation
from hapic.decorator import DECORATION_ATTRIBUTE_NAME
from hapic.decorator import DecoratedController
from hapic.error.main import ErrorBuilderInterface
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
from hapic.exception import NoRoutesException
from hapic.exception import OutputValidationException
from hapic.exception import RouteNotFound
from hapic.processor.main import ProcessValidationError
from hapic.processor.main import RequestParameters

try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus


# Bottle regular expression to locate url parameters
BOTTLE_RE_PATH_URL = re.compile(r"<([^:<>]+)(?::[^<>]+)?>")


class BottleContext(BaseContext):
    def __init__(
        self,
        app: bottle.Bottle,
        default_error_builder: ErrorBuilderInterface = None,
        debug: bool = False,
    ):
        super().__init__()
        self._handled_exceptions = (
            []
        )  # type: typing.List[HandledException]  # nopep8
        self._exceptions_handler_installed = False
        self.app = app
        self.default_error_builder = (
            default_error_builder or MarshmallowDefaultErrorBuilder()
        )  # FDV
        self.debug = debug

    def get_request_parameters(self, *args, **kwargs) -> RequestParameters:
        path_parameters = dict(bottle.request.url_args)
        query_parameters = MultiDict(bottle.request.query.allitems())
        body_parameters = dict(bottle.request.json or {})
        form_parameters = MultiDict(bottle.request.forms.allitems())
        header_parameters = dict(bottle.request.headers)
        files_parameters = dict(bottle.request.files)

        return RequestParameters(
            path_parameters=path_parameters,
            query_parameters=query_parameters,
            body_parameters=body_parameters,
            form_parameters=form_parameters,
            header_parameters=header_parameters,
            files_parameters=files_parameters,
        )

    def get_response(
        self, response: str, http_code: int, mimetype: str = "application/json"
    ) -> bottle.HTTPResponse:
        return bottle.HTTPResponse(
            body=response,
            headers=[("Content-Type", mimetype)],
            status=http_code,
        )

    def get_validation_error_response(
        self,
        error: ProcessValidationError,
        http_code: HTTPStatus = HTTPStatus.BAD_REQUEST,
    ) -> typing.Any:
        dumped_error = self._get_dumped_error_from_validation_error(error)
        return bottle.HTTPResponse(
            body=json.dumps(dumped_error),
            headers=[("Content-Type", "application/json")],
            status=int(http_code),
        )

    def find_route(
        self, decorated_controller: DecoratedController
    ) -> RouteRepresentation:
        if not self.app.routes:
            raise NoRoutesException("There is no routes in your bottle app")

        reference = decorated_controller.reference
        for route in self.app.routes:
            route_token = getattr(
                route.callback, DECORATION_ATTRIBUTE_NAME, None
            )

            match_with_wrapper = route.callback == reference.wrapper
            match_with_wrapped = route.callback == reference.wrapped
            match_with_token = route_token == reference.token

            if match_with_wrapper or match_with_wrapped or match_with_token:
                return RouteRepresentation(
                    rule=self.get_swagger_path(route.rule),
                    method=route.method.lower(),
                    original_route_object=route,
                )
        # TODO BS 20171010: Raise exception or print error ? see #10
        raise RouteNotFound(
            'Decorated route "{}" was not found in bottle routes'.format(
                decorated_controller.name
            )
        )

    def get_swagger_path(self, contextualised_rule: str) -> str:
        return BOTTLE_RE_PATH_URL.sub(r"{\1}", contextualised_rule)

    def by_pass_output_wrapping(self, response: typing.Any) -> bool:
        if isinstance(response, bottle.HTTPResponse):
            return True
        return False

    def _add_exception_class_to_catch(
        self, exception_class: typing.Type[Exception], http_code: int
    ) -> None:
        if not self._exceptions_handler_installed:
            self._install_exceptions_handler()

        self._handled_exceptions.append(
            HandledException(exception_class, http_code)
        )

    def _install_exceptions_handler(self) -> None:
        """
        Setup the bottle app to enable exception catching with internal
        hapic exception catcher.
        """
        self.app.install(self.handle_exceptions_decorator_builder)

    def _get_handled_exception_class_and_http_codes(
        self,
    ) -> typing.List[HandledException]:
        """
        See hapic.context.BaseContext#_get_handled_exception_class_and_http_codes  # nopep8
        """
        return self._handled_exceptions

    def is_debug(self) -> bool:
        return self.debug
