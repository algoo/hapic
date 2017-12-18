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
from hapic.processor import RequestParameters
from hapic.processor import ProcessValidationError

if typing.TYPE_CHECKING:
    from pyramid.response import Response
    from pyramid.config import Configurator

# Bottle regular expression to locate url parameters
PYRAMID_RE_PATH_URL = re.compile(r'')


class PyramidContext(ContextInterface):
    def __init__(self, configurator: 'Configurator'):
        self.configurator = configurator

    def get_request_parameters(self, *args, **kwargs) -> RequestParameters:
        req = args[-1]  # TODO : Check
        # TODO : move this code to check_json
        # same idea as in : https://bottlepy.org/docs/dev/_modules/bottle.html#BaseRequest.json
        if req.body and req.content_type in ('application/json', 'application/json-rpc'):
            json_body = req.json_body
            # TODO : raise exception if not correct , return 400 if uncorrect instead ?
        else:
            json_body = {}

        return RequestParameters(
            path_parameters=req.matchdict,
            query_parameters=req.GET,
            body_parameters=json_body,
            form_parameters=req.POST,
            header_parameters=req.headers,
            files_parameters={},  # TODO - G.M - 2017-11-05 - Code it
        )

    def get_response(
        self,
        response: dict,
        http_code: int,
    ) -> 'Response':
        from pyramid.response import Response
        return Response(
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
        from pyramid.response import Response
        from hapic.hapic import _default_global_error_schema
        unmarshall = _default_global_error_schema.dump(error)
        if unmarshall.errors:
            raise OutputValidationException(
                'Validation error during dump of error response: {}'.format(
                    str(unmarshall.errors)
                )
            )

        return Response(
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
        for category in self.configurator.introspector.get_category('views'):
            view_intr = category['introspectable']
            route_intr = category['related']

            reference = decorated_controller.reference
            route_token = getattr(
                view_intr.get('callable'),
                DECORATION_ATTRIBUTE_NAME,
                None,
            )

            match_with_wrapper = view_intr.get('callable') == reference.wrapper
            match_with_wrapped = view_intr.get('callable') == reference.wrapped
            match_with_token = route_token == reference.token

            if match_with_wrapper or match_with_wrapped or match_with_token:
                # TODO BS 20171107: C'est une liste de route sous pyramid !!!
                # Mais de toute maniere les framework womme pyramid, flask
                # peuvent avoir un controlleur pour plusieurs routes doc
                # .find_route doit retourner une liste au lieu d'une seule
                # route
                route_pattern = route_intr[0].get('pattern')
                route_method = route_intr[0].get('request_methods')[0]

                return RouteRepresentation(
                    rule=self.get_swagger_path(route_pattern),
                    method=route_method,
                    original_route_object=route_intr[0],
                )

    def get_swagger_path(self, contextualised_rule: str) -> str:
        # TODO BS 20171110: Pyramid allow route like '/{foo:\d+}', so adapt
        # and USE regular expression (see https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/urldispatch.html#custom-route-predicates)  # nopep8
        return contextualised_rule

    def by_pass_output_wrapping(self, response: typing.Any) -> bool:
        return False
