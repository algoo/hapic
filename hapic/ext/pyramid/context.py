# -*- coding: utf-8 -*-
import json
import re
import typing

try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus

from hapic.context import BaseContext
from hapic.context import RouteRepresentation
from hapic.decorator import DecoratedController
from hapic.decorator import DECORATION_ATTRIBUTE_NAME
from hapic.exception import OutputValidationException
from hapic.processor import RequestParameters
from hapic.processor import ProcessValidationError
from hapic.error import DefaultErrorBuilder
from hapic.error import ErrorBuilderInterface

if typing.TYPE_CHECKING:
    from pyramid.response import Response
    from pyramid.config import Configurator

# Bottle regular expression to locate url parameters
PYRAMID_RE_PATH_URL = re.compile(r'')


class PyramidContext(BaseContext):
    def __init__(
        self,
        configurator: 'Configurator',
        default_error_builder: ErrorBuilderInterface = None,
        debug: bool = False,
    ):
        self._handled_exceptions = []  # type: typing.List[HandledException]  # nopep8
        self.configurator = configurator
        self.default_error_builder = \
            default_error_builder or DefaultErrorBuilder()  # FDV
        self.debug = debug

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
        response: str,
        http_code: int,
        mimetype: str='application/json',
    ) -> 'Response':
        # INFO - G.M - 20-04-2018 - No message_body for some http code,
        # no Content-Type needed if no content
        # see: https://tools.ietf.org/html/rfc2616#section-4.3
        if http_code in [204, 304] or (100 <= http_code <= 199):
            headers = []
        else:
            headers = [
                ('Content-Type', mimetype),
            ]
        from pyramid.response import Response
        return Response(
            body=response,
            headers=headers,
            status=http_code,
        )

    def get_validation_error_response(
        self,
        error: ProcessValidationError,
        http_code: HTTPStatus=HTTPStatus.BAD_REQUEST,
    ) -> typing.Any:
        from pyramid.response import Response

        error_content = self.default_error_builder.build_from_validation_error(
            error,
        )

        # Check error
        dumped = self.default_error_builder.dump(error).data
        unmarshall = self.default_error_builder.load(dumped)
        if unmarshall.errors:
            raise OutputValidationException(
                'Validation error during dump of error response: {}'.format(
                    str(unmarshall.errors)
                )
            )

        return Response(
            body=json.dumps(error_content),
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

        # INFO - G.M - 27-04-2018 - route_pattern of pyramid without '/' case.
        # For example, when using config.include with route_prefix param,
        # there is no '/' at beginning of the path.
        if contextualised_rule[0] != '/':
            contextualised_rule = '/{}'.format(contextualised_rule)
        return contextualised_rule

    def by_pass_output_wrapping(self, response: typing.Any) -> bool:
        return False

    def add_view(
        self,
        route: str,
        http_method: str,
        view_func: typing.Callable[..., typing.Any],
    ) -> None:

        self.configurator.add_route(
            name=route,
            path=route,
            request_method=http_method
        )

        self.configurator.add_view(
            view_func,
            route_name=route,
        )

    def serve_directory(
        self,
        route_prefix: str,
        directory_path: str,
    ) -> None:
        self.configurator.add_static_view(
            name=route_prefix,
            path=directory_path,
        )

    def _add_exception_class_to_catch(
        self,
        exception_class: typing.Type[Exception],
        http_code: int,
    ) -> None:
        def factory_view_func(exception_class, http_code):
            def view_func(exc, request):
                # TODO BS 2018-05-04: How to be attentive to hierarchy ?
                error_builder = self.get_default_error_builder()
                error_body = error_builder.build_from_exception(
                    exc,
                    include_traceback=self.is_debug(),
                )
                return self.get_response(
                    json.dumps(error_body),
                    http_code
                )
            return view_func

        self.configurator.add_view(
            view=factory_view_func(
                exception_class,
                http_code,
            ),
            context=exception_class,
        )

    def is_debug(self) -> bool:
        return self.debug
