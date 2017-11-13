# -*- coding: utf-8 -*-
import json
import typing
from http import HTTPStatus

import bottle

from hapic.context import ContextInterface
from hapic.exception import OutputValidationException
from hapic.processor import RequestParameters, ProcessValidationError


class BottleContext(ContextInterface):
    def get_request_parameters(self, *args, **kwargs) -> RequestParameters:
        path_parameters = dict(bottle.request.url_args)
        query_parameters = bottle.MultiDict(bottle.request.query)
        body_parameters = dict(bottle.request.json or {})
        form_parameters = bottle.MultiDict(bottle.request.forms)
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
