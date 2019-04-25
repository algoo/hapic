# -*- coding: utf-8 -*-
import cgi
import json
import logging
import re
import traceback
import typing

from hapic.context import BaseContext
from hapic.context import RouteRepresentation
from hapic.data import HapicFile
from hapic.decorator import DECORATION_ATTRIBUTE_NAME
from hapic.decorator import DecoratedController
from hapic.error.main import ErrorBuilderInterface
from hapic.processor.main import Processor
from hapic.processor.main import ProcessValidationError
from hapic.processor.main import RequestParameters
from hapic.util import LOGGER_NAME
from hapic.util import LowercaseKeysDict

try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus


if typing.TYPE_CHECKING:
    from pyramid.response import Response
    from pyramid.config import Configurator
    from hapic.context import HandledException  # noqa: F401

# Bottle regular expression to locate url parameters
PYRAMID_RE_PATH_URL = re.compile(r"")


class PyramidContext(BaseContext):
    def __init__(
        self,
        configurator: "Configurator",
        processor_class: typing.Optional[typing.Type[Processor]] = None,
        default_error_builder: ErrorBuilderInterface = None,
        debug: bool = False,
    ):
        super().__init__(processor_class, default_error_builder)
        self._handled_exceptions = []  # type: typing.List[HandledException]
        self.configurator = configurator
        self.debug = debug

    def get_request_parameters(self, *args, **kwargs) -> RequestParameters:
        req = args[-1]  # TODO : Check
        # TODO : move this code to check_json
        # same idea as in : https://bottlepy.org/docs/dev/_modules/bottle.html#BaseRequest.json
        if req.body and req.content_type in ("application/json", "application/json-rpc"):
            json_body = req.json_body
            # TODO : raise exception if not correct , return 400 if uncorrect instead ?
        else:
            json_body = {}

        forms_parameters = {}
        files_parameters = {}
        for name, item in req.POST.items():
            if isinstance(item, cgi.FieldStorage):
                files_parameters[name] = item
            else:
                forms_parameters[name] = item

        return RequestParameters(
            path_parameters=req.matchdict,
            query_parameters=req.GET,
            body_parameters=json_body,
            form_parameters=req.POST,
            header_parameters=LowercaseKeysDict([(k.lower(), v) for k, v in req.headers.items()]),
            files_parameters=files_parameters,
        )

    def get_response(
        self, response: str, http_code: int, mimetype: str = "application/json"
    ) -> "Response":
        # INFO - G.M - 20-04-2018 - No message_body for some http code,
        # no Content-Type needed if no content
        # see: https://tools.ietf.org/html/rfc2616#section-4.3
        if http_code in [204, 304] or (100 <= http_code <= 199):
            headers = []
        else:
            headers = [("Content-Type", mimetype)]
        from pyramid.response import Response

        return Response(body=response, headers=headers, status=http_code)

    def get_file_response(self, file_response: HapicFile, http_code: int):
        if file_response.file_path:
            from pyramid.response import FileResponse

            # TODO - G.M - 2019-03-27 - add support for overriding parameters of
            # file_response like content_length
            # Extended support for file response:
            # https://github.com/algoo/hapic/issues/171
            response = FileResponse(
                path=file_response.file_path,
                # INFO - G.M - 2018-09-13 - If content_type is no, mimetype
                # is automatically guessed
                content_type=file_response.mimetype or None,
            )
        else:
            from pyramid.response import FileIter
            from pyramid.response import Response

            response = Response(status=http_code)
            response.content_type = file_response.mimetype
            response.app_iter = FileIter(file_response.file_object)

        if file_response.content_length:
            response.content_length = file_response.content_length
        if file_response.last_modified:
            response.last_modified = file_response.last_modified

        response.status_code = http_code
        response.content_disposition = file_response.get_content_disposition_header_value()
        return response

    def get_validation_error_response(
        self, error: ProcessValidationError, http_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    ) -> typing.Any:
        from pyramid.response import Response

        dumped_error = self._get_dumped_error_from_validation_error(error)
        return Response(
            body=json.dumps(dumped_error),
            headers=[("Content-Type", "application/json")],
            status=int(http_code),
        )

    def find_route(self, decorated_controller: DecoratedController) -> RouteRepresentation:
        for category in self.configurator.introspector.get_category("views"):
            view_intr = category["introspectable"]
            route_intr = category["related"]

            reference = decorated_controller.reference
            route_token = getattr(view_intr.get("callable"), DECORATION_ATTRIBUTE_NAME, None)

            match_with_wrapper = view_intr.get("callable") == reference.wrapper
            match_with_wrapped = view_intr.get("callable") == reference.wrapped
            match_with_token = route_token == reference.token

            if match_with_wrapper or match_with_wrapped or match_with_token:
                # TODO BS 20171107: C'est une liste de route sous pyramid !!!
                # Mais de toute maniere les framework womme pyramid, flask
                # peuvent avoir un controlleur pour plusieurs routes doc
                # .find_route doit retourner une liste au lieu d'une seule
                # route
                route_pattern = route_intr[0].get("pattern")
                route_method = route_intr[0].get("request_methods")[0]

                return RouteRepresentation(
                    rule=self.get_swagger_path(route_pattern),
                    method=route_method,
                    original_route_object=route_intr[0],
                )

    def get_swagger_path(self, contextualised_rule: str) -> str:
        # TODO BS 20171110: Pyramid allow route like '/{foo:\d+}', so adapt
        # and USE regular expression (see https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/urldispatch.html#custom-route-predicates)

        # INFO - G.M - 27-04-2018 - route_pattern of pyramid without '/' case.
        # For example, when using config.include with route_prefix param,
        # there is no '/' at beginning of the path.
        if contextualised_rule[0] != "/":
            contextualised_rule = "/{}".format(contextualised_rule)
        return contextualised_rule

    def by_pass_output_wrapping(self, response: typing.Any) -> bool:
        from pyramid.response import Response

        return isinstance(response, Response)

    def add_view(
        self, route: str, http_method: str, view_func: typing.Callable[..., typing.Any]
    ) -> None:

        self.configurator.add_route(name=route, path=route, request_method=http_method)

        self.configurator.add_view(view_func, route_name=route)

    def serve_directory(self, route_prefix: str, directory_path: str) -> None:
        self.configurator.add_static_view(name=route_prefix, path=directory_path)

    def _add_exception_class_to_catch(
        self, exception_class: typing.Type[Exception], http_code: int
    ) -> None:
        def factory_view_func(exception_class, http_code):
            def view_func(exc, request):
                # TODO - G.M - 2018-09-28 - move logging code outside of
                # specific framework context.
                # see https://github.com/algoo/hapic/issues/93
                logger = logging.getLogger(LOGGER_NAME)
                logger.info(
                    "Exception {exc} occured, return {http_code} http_code : {msg}".format(
                        exc=type(exc).__name__, http_code=http_code, msg=str(exc)
                    )
                )
                logger.debug(traceback.format_exc())
                # TODO BS 2018-05-04: How to be attentive to hierarchy ?
                error_builder = self.default_error_builder
                error_body = error_builder.build_from_exception(
                    exc, include_traceback=self.is_debug()
                )
                return self.get_response(json.dumps(error_body), http_code)

            return view_func

        self.configurator.add_view(
            view=factory_view_func(exception_class, http_code), context=exception_class
        )

    def is_debug(self) -> bool:
        return self.debug
