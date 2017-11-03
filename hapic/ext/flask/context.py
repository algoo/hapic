# -*- coding: utf-8 -*-
import json
import typing
from http import HTTPStatus

from flask import request, Response


from hapic.context import ContextInterface
from hapic.exception import OutputValidationException
from hapic.processor import RequestParameters, ProcessValidationError


class FlaskContext(ContextInterface):
    def get_request_parameters(self, *args, **kwargs) -> RequestParameters:
        return RequestParameters(
            path_parameters=request.view_args,
            query_parameters=request.args,  # TODO: Check
            body_parameters=request.get_json(),  # TODO: Check
            form_parameters=request.form,
            header_parameters=request.headers,
        )

    def get_response(
        self,
        response: dict,
        http_code: int,
    ) -> Response:
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
        return Response(
            response=json.dumps(unmarshall.data),
            mimetype='application/json',
            status=int(http_code),
        )
