# -*- coding: utf-8 -*-
import json
import typing
from http import HTTPStatus

from pyramid.request import Request
from pyramid.response import Response


from hapic.context import ContextInterface
from hapic.exception import OutputValidationException
from hapic.processor import RequestParameters, ProcessValidationError


class PyramidContext(ContextInterface):
    def get_request_parameters(self, *args, **kwargs) -> RequestParameters:
        req = args[-1]  # TODO : Check
        assert isinstance(req, Request)
        # TODO : move this code to check_json
        # same idea as in : https://bottlepy.org/docs/dev/_modules/bottle.html#BaseRequest.json
        if req.body and req.content_type in ('application/json', 'application/json-rpc'):
            json_body = req.json_body
            # TODO : raise exception if not correct , return 400 if uncorrect instead ?
        else:
            json_body = None

        return RequestParameters(
            path_parameters=req.matchdict,
            query_parameters=req.GET,
            body_parameters=json_body,
            form_parameters=req.POST,
            header_parameters=req.headers,
        )

    def get_response(
        self,
        response: dict,
        http_code: int,
    ) -> Response:
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
