# -*- coding: utf-8 -*-
from datetime import datetime
import typing
import urllib.parse


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
        content_length: int = None,
        last_modified: datetime = None,
        as_attachment: bool = False,
        use_conditional_response: bool = True,
        etag: typing.Optional[str] = None,
    ):
        """
        Framework Representation of a file, allowing similar support for different
        framework.
        You should provided either file_path or file_object.

        :file_path: path of the file
        :file_object: File Object of the file
        :mimetype: Mimetype of the returned file
        :filename: filename of the returned file.
        :content_length: full length of the file, may be modified after check if use_conditional_response
        is activated (for example if you provide a 200 byte range, you will get a length of 200,
        instead of the value given here)
        :param as_attachment: set the disposition as attachment in order to force browser
        to download file
        :param use_conditional_response: active support of theses advanced feature: Range,
        If-Modified-Since, If-None-Match, see RFC-7233
        :param etag: Id of the file, used by conditional response to not return same file.
        """
        self.file_path = file_path
        self.file_object = file_object
        self.filename = filename
        self.mimetype = mimetype
        self.as_attachment = as_attachment
        self.last_modified = last_modified
        self.content_length = content_length
        self.use_conditional_response = use_conditional_response
        self.etag = etag

    def get_content_disposition_header_value(self) -> str:
        disposition = "inline"
        if self.as_attachment:
            disposition = "attachment"
        if self.filename:
            # INFO - G.M - 2018-10-26 - deal correctly with unicode filename
            # see rfc6266 for more info.
            ascii_filename = self.filename.encode("ascii", "replace").decode()
            # INFO - G.M - 2018-10-30 - Format correctly unicode.
            # encoding is needed for correct unicode character support,
            # Percent-encoding is best pratices, see also rfc5987.
            urlencoded_unicode_filename = urllib.parse.quote(self.filename)

            disposition = "{}; filename=\"{}\"; filename*=UTF-8''{};".format(
                disposition, ascii_filename, urlencoded_unicode_filename
            )
        return disposition
