# coding: utf-8
import asyncio
import typing
from http import HTTPStatus
from json import JSONDecodeError

from aiohttp.web_request import Request
from multidict import MultiDict

from hapic.context import BaseContext
from hapic.context import RouteRepresentation
from hapic.decorator import DecoratedController
from hapic.exception import WorkflowException
from hapic.processor import ProcessValidationError
from hapic.processor import RequestParameters
from aiohttp import web


class AiohttpContext(BaseContext):
    def __init__(
        self,
        app: web.Application,
    ) -> None:
        self._app = app

    @property
    def app(self) -> web.Application:
        return self._app

    async def get_request_parameters(
        self,
        *args,
        **kwargs
    ) -> RequestParameters:
        try:
            request = args[0]
        except IndexError:
            raise WorkflowException(
                'Unable to get aiohttp request object',
            )
        request = typing.cast(Request, request)

        path_parameters = dict(request.match_info)
        query_parameters = MultiDict(request.query.items())

        if request.can_read_body:
            try:
                # FIXME NOW: request.json() make
                # request.content empty, do it ONLY if json headers
                # body_parameters = await request.json()
                # body_parameters = await request.content.read()
                body_parameters = {}
                pass
            except JSONDecodeError:
                # FIXME BS 2018-07-13: Raise an 400 error if header contain
                # json type
                body_parameters = {}
        else:
            body_parameters = {}

        form_parameters_multi_dict_proxy = await request.post()
        form_parameters = MultiDict(form_parameters_multi_dict_proxy.items())
        header_parameters = dict(request.headers.items())

        # TODO BS 2018-07-13: Manage files (see
        # https://docs.aiohttp.org/en/stable/multipart.html)
        files_parameters = dict()

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
        response: str,
        http_code: int,
        mimetype: str = 'application/json',
    ) -> typing.Any:
        pass

    def get_validation_error_response(
        self,
        error: ProcessValidationError,
        http_code: HTTPStatus = HTTPStatus.BAD_REQUEST,
    ) -> typing.Any:
        pass

    def find_route(
        self,
        decorated_controller: DecoratedController,
    ) -> RouteRepresentation:
        pass

    def get_swagger_path(
        self,
        contextualised_rule: str,
    ) -> str:
        pass

    def by_pass_output_wrapping(
        self,
        response: typing.Any,
    ) -> bool:
        pass

    def add_view(
        self,
        route: str,
        http_method: str,
        view_func: typing.Callable[..., typing.Any],
    ) -> None:
        pass

    def serve_directory(
        self,
        route_prefix: str,
        directory_path: str,
    ) -> None:
        pass

    def is_debug(
        self,
    ) -> bool:
        pass

    def handle_exception(
        self,
        exception_class: typing.Type[Exception],
        http_code: int,
    ) -> None:
        pass

    def handle_exceptions(
        self,
        exception_classes: typing.List[typing.Type[Exception]],
        http_code: int,
    ) -> None:
        pass
