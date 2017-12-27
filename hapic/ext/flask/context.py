# -*- coding: utf-8 -*-
import json
import re
import typing
try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus

from hapic.context import ContextInterface
from hapic.context import RouteRepresentation
from hapic.decorator import DecoratedController
from hapic.decorator import DECORATION_ATTRIBUTE_NAME
from hapic.exception import OutputValidationException
from hapic.processor import RequestParameters, ProcessValidationError
from flask import Flask

if typing.TYPE_CHECKING:
    from flask import Response

# flask regular expression to locate url parameters
FLASK_RE_PATH_URL = re.compile(r'<(?:[^:<>]+:)?([^<>]+)>')


class FlaskContext(ContextInterface):
    def __init__(self, app: Flask):
        self.app = app

    def get_request_parameters(self, *args, **kwargs) -> RequestParameters:
        from flask import request
        return RequestParameters(
            path_parameters=request.view_args,
            query_parameters=request.args,  # TODO: Check
            body_parameters=request.get_json(),  # TODO: Check
            form_parameters=request.form,
            header_parameters=request.headers,
            files_parameters={},  # TODO: BS 20171115: Code it
        )

    def get_response(
        self,
        response: dict,
        http_code: int,
    ) -> 'Response':
        from flask import Response
        return Response(
            response=json.dumps(response),
            mimetype='application/json',
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
        from flask import Response
        return Response(
            response=json.dumps(unmarshall.data),
            mimetype='application/json',
            status=int(http_code),
        )

    def find_route(
        self,
        decorated_controller: 'DecoratedController',
    ):
        reference = decorated_controller.reference
        for route in self.app.url_map.iter_rules():
            if route.endpoint not in self.app.view_functions:
                continue
            route_callback = self.app.view_functions[route.endpoint]
            route_token = getattr(
                route_callback,
                DECORATION_ATTRIBUTE_NAME,
                None,
            )
            match_with_wrapper = route_callback == reference.wrapper
            match_with_wrapped = route_callback == reference.wrapped
            match_with_token = route_token == reference.token

            # FIXME - G.M - 2017-12-04 - return list instead of one method
            # This fix, return only 1 allowed method, change this when
            # RouteRepresentation is adapted to return multiples methods.
            method = [x for x in route.methods
                      if x not in ['OPTIONS', 'HEAD']][0]

            if match_with_wrapper or match_with_wrapped or match_with_token:
                return RouteRepresentation(
                    rule=self.get_swagger_path(route.rule),
                    method=method,
                    original_route_object=route,
                )

    def get_swagger_path(self, contextualised_rule: str) -> str:
        # TODO - G.M - 2017-12-05 Check if all route path are handled correctly
        return FLASK_RE_PATH_URL.sub(r'{\1}', contextualised_rule)

    def by_pass_output_wrapping(self, response: typing.Any) -> bool:
        return isinstance(response, Response)
