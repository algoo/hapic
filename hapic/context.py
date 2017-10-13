# -*- coding: utf-8 -*-
import json
import typing
from http import HTTPStatus

import bottle

from hapic.exception import OutputValidationException
# from hapic.hapic import _default_global_error_schema
from hapic.processor import RequestParameters, ProcessValidationError


class ContextInterface(object):
    def get_request_parameters(self, *args, **kwargs) -> RequestParameters:
        raise NotImplementedError()

    def get_response(
        self,
        response: dict,
        http_code: int,
    ) -> typing.Any:
        raise NotImplementedError()

    def get_validation_error_response(
        self,
        error: ProcessValidationError,
        http_code: HTTPStatus=HTTPStatus.BAD_REQUEST,
    ) -> typing.Any:
        raise NotImplementedError()
