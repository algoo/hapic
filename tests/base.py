# -*- coding: utf-8 -*-
import json
import typing


try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus

from multidict import MultiDict

from hapic.ext.bottle import BottleContext
from hapic.processor import RequestParameters
from hapic.processor import ProcessValidationError
from hapic.context import HandledException


class Base(object):
    pass


# TODO BS 20171105: Make this bottle agnostic !
class MyContext(BottleContext):
    def __init__(
        self,
        app,
        fake_path_parameters=None,
        fake_query_parameters=None,
        fake_body_parameters=None,
        fake_form_parameters=None,
        fake_header_parameters=None,
        fake_files_parameters=None,
    ) -> None:
        super().__init__(app=app)
        self._handled_exceptions = []  # type: typing.List[HandledException]  # nopep8
        self._exceptions_handler_installed = False
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

    def get_validation_error_response(
        self,
        error: ProcessValidationError,
        http_code: HTTPStatus=HTTPStatus.BAD_REQUEST,
    ) -> typing.Any:
        return self.get_response(
            response=json.dumps({
                'original_error': {
                    'details': error.details,
                    'message': error.message,
                },
                'http_code': http_code,
            }),
            http_code=http_code,
        )

    def _add_exception_class_to_catch(
        self,
        exception_class: typing.Type[Exception],
        http_code: int,
    ) -> None:
        if not self._exceptions_handler_installed:
            self._install_exceptions_handler()
        self._handled_exceptions.append(
            HandledException(exception_class, http_code),
        )

    def _get_handled_exception_class_and_http_codes(
        self,
    ) -> typing.List[HandledException]:
        return self._handled_exceptions
