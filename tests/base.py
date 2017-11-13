# -*- coding: utf-8 -*-
import typing
from http import HTTPStatus

from multidict import MultiDict

from hapic.context import ContextInterface
from hapic.processor import RequestParameters
from hapic.processor import ProcessValidationError


class Base(object):
    pass


class MyContext(ContextInterface):
    def __init__(
        self,
        fake_path_parameters=None,
        fake_query_parameters=None,
        fake_body_parameters=None,
        fake_form_parameters=None,
        fake_header_parameters=None,
        fake_files_parameters=None,
    ) -> None:
        self.fake_path_parameters = fake_path_parameters or {}
        self.fake_query_parameters = fake_query_parameters or MultiDict()
        self.fake_body_parameters = fake_body_parameters or {}
        self.fake_form_parameters = fake_form_parameters or MultiDict()
        self.fake_header_parameters = fake_header_parameters or {}
        self.fake_files_parameters = fake_files_parameters or {}

    def get_request_parameters(self, *args, **kwargs) -> RequestParameters:
        return RequestParameters(
            path_parameters=self.fake_path_parameters,
            query_parameters=self.fake_query_parameters,
            body_parameters=self.fake_body_parameters,
            form_parameters=self.fake_form_parameters,
            header_parameters=self.fake_header_parameters,
            files_parameters=self.fake_files_parameters,
        )

    def get_response(
        self,
        response: dict,
        http_code: int,
    ) -> typing.Any:
        return {
            'original_response': response,
            'http_code': http_code,
        }

    def get_validation_error_response(
        self,
        error: ProcessValidationError,
        http_code: HTTPStatus=HTTPStatus.BAD_REQUEST,
    ) -> typing.Any:
        return {
            'original_error': error,
            'http_code': http_code,
        }
