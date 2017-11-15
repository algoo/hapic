# -*- coding: utf-8 -*-
import typing

if typing.TYPE_CHECKING:
    from hapic.decorator import ControllerWrapper


class Description(object):
    def __init__(self, wrapper: 'ControllerWrapper') -> None:
        self.wrapper = wrapper


class InputPathDescription(Description):
    pass


class InputQueryDescription(Description):
    pass


class InputBodyDescription(Description):
    pass


class InputHeadersDescription(Description):
    pass


class InputFormsDescription(Description):
    pass


class InputFilesDescription(Description):
    pass


class OutputBodyDescription(Description):
    pass


class OutputFileDescription(Description):
    pass


class OutputHeadersDescription(Description):
    pass


class ErrorDescription(Description):
    pass


class ControllerDescription(object):
    def __init__(
        self,
        input_path: InputPathDescription=None,
        input_query: InputQueryDescription=None,
        input_body: InputBodyDescription=None,
        input_headers: InputHeadersDescription=None,
        input_forms: InputFormsDescription=None,
        input_files: InputFilesDescription=None,
        output_body: OutputBodyDescription=None,
        output_file: OutputFileDescription=None,
        output_headers: OutputHeadersDescription=None,
        errors: typing.List[ErrorDescription]=None,
    ):
        self.input_path = input_path
        self.input_query = input_query
        self.input_body = input_body
        self.input_headers = input_headers
        self.input_forms = input_forms
        self.input_files = input_files
        self.output_body = output_body
        self.output_file = output_file
        self.output_headers = output_headers
        self.errors = errors or []
