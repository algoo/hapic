# -*- coding: utf-8 -*-
import json
import re
import typing
try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus

import bottle
from multidict import MultiDict

from hapic.context import ContextInterface
from hapic.context import RouteRepresentation
from hapic.decorator import DecoratedController
from hapic.decorator import DECORATION_ATTRIBUTE_NAME
from hapic.exception import OutputValidationException
from hapic.exception import NoRoutesException
from hapic.exception import RouteNotFound
from hapic.processor import RequestParameters
from hapic.processor import ProcessValidationError

# Bottle regular expression to locate url parameters
BOTTLE_RE_PATH_URL = re.compile(r'<([^:<>]+)(?::[^<>]+)?>')


class BottleContext(ContextInterface):
    def __init__(self, app: bottle.Bottle):
        self.app = app

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
        self,
        response: dict,
        http_code: int,
    ) -> bottle.HTTPResponse:
        return bottle.HTTPResponse(
            body=json.dumps(response),
            headers=[
                ('Content-Type', 'application/json'),
            ],
            status=http_code,
        )

    def get_validation_error_response(
        self,
        error: ProcessValidationError,
        http_code: HTTPStatus=HTTPStatus.BAD_REQUEST,
    ) -> typing.Any:
        # TODO BS 20171010: Manage error schemas, see #4
        from hapic.hapic import _default_global_error_schema
        unmarshall = _default_global_error_schema.dump(error)
        if unmarshall.errors:
            raise OutputValidationException(
                'Validation error during dump of error response: {}'.format(
                    str(unmarshall.errors)
                )
            )

        return bottle.HTTPResponse(
            body=json.dumps(unmarshall.data),
            headers=[
                ('Content-Type', 'application/json'),
            ],
            status=int(http_code),
        )

    def find_route(
        self,
        decorated_controller: DecoratedController,
    ) -> RouteRepresentation:
        if not self.app.routes:
            raise NoRoutesException('There is no routes in your bottle app')

        reference = decorated_controller.reference
        for route in self.app.routes:
            route_token = getattr(
                route.callback,
                DECORATION_ATTRIBUTE_NAME,
                None,
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
                decorated_controller.name,
            )
        )

    def get_swagger_path(self, contextualised_rule: str) -> str:
        return BOTTLE_RE_PATH_URL.sub(r'{\1}', contextualised_rule)

    def by_pass_output_wrapping(self, response: typing.Any) -> bool:
        if isinstance(response, bottle.HTTPResponse):
            return True
        return False
