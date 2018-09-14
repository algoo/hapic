# -*- coding: utf-8 -*-
import typing


class HapicData(object):
    def __init__(self):
        self.body = {}
        self.path = {}
        self.query = {}
        self.headers = {}
        self.forms = {}
        self.files = {}


class HapicFile(object):
    def __init__(
        self,
        file_path: typing.Optional[str] = None,
        file_object: typing.Any = None,
        mimetype: typing.Any = None,
        filename: str = None,
        as_attachment: bool = False,
    ):
        self.file_path = file_path
        self.file_object = file_object
        self.filename = filename
        self.mimetype = mimetype
        self.as_attachment = as_attachment

    def get_content_disposition_header_value(self) -> str:
        disposition = 'inline'
        if self.as_attachment:
            disposition = 'attachment'
        if self.filename:
            disposition = '{}; filename="{}"'.format(disposition, self.filename)
        return disposition
