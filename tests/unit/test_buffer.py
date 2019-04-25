# -*- coding: utf-8 -*-
from unittest import mock

import pytest

from hapic.buffer import DecorationBuffer
from hapic.description import ErrorDescription
from hapic.description import InputBodyDescription
from hapic.description import InputFormsDescription
from hapic.description import InputHeadersDescription
from hapic.description import InputPathDescription
from hapic.description import InputQueryDescription
from hapic.description import OutputBodyDescription
from hapic.description import OutputHeadersDescription
from hapic.exception import AlreadyDecoratedException
from tests.base import Base

fake_controller_wrapper = mock.MagicMock()


class TestBuffer(Base):
    def test_unit__buffer_usage__ok__set_descriptions(self):
        buffer = DecorationBuffer()

        input_path_description = InputPathDescription(fake_controller_wrapper)
        input_query_description = InputQueryDescription(fake_controller_wrapper)
        input_body_description = InputBodyDescription(fake_controller_wrapper)
        input_headers_description = InputHeadersDescription(fake_controller_wrapper)
        input_forms_description = InputFormsDescription(fake_controller_wrapper)
        output_headers_description = OutputHeadersDescription(fake_controller_wrapper)
        output_body_description = OutputBodyDescription(fake_controller_wrapper)
        error_description = ErrorDescription(fake_controller_wrapper)

        buffer.input_path = input_path_description
        buffer.input_query = input_query_description
        buffer.input_body = input_body_description
        buffer.input_headers = input_headers_description
        buffer.input_forms = input_forms_description
        buffer.output_headers = output_headers_description
        buffer.output_body = output_body_description
        buffer.add_error(error_description)

        description = buffer.get_description()
        assert description.input_path == input_path_description
        assert description.input_query == input_query_description
        assert description.input_body == input_body_description
        assert description.input_headers == input_headers_description
        assert description.input_forms == input_forms_description
        assert description.output_headers == output_headers_description
        assert description.output_body == output_body_description
        assert description.errors == [error_description]

        buffer.clear()
        description = buffer.get_description()

        assert description.input_path is None
        assert description.input_query is None
        assert description.input_body is None
        assert description.input_headers is None
        assert description.input_forms is None
        assert description.output_headers is None
        assert description.output_body is None
        assert description.errors == []

    def test_unit__buffer_usage__error__cant_replace(self):
        buffer = DecorationBuffer()

        input_path_description = InputPathDescription(fake_controller_wrapper)
        input_query_description = InputQueryDescription(fake_controller_wrapper)
        input_body_description = InputBodyDescription(fake_controller_wrapper)
        input_headers_description = InputHeadersDescription(fake_controller_wrapper)
        input_forms_description = InputFormsDescription(fake_controller_wrapper)
        output_headers_description = OutputHeadersDescription(fake_controller_wrapper)
        output_body_description = OutputBodyDescription(fake_controller_wrapper)

        buffer.input_path = input_path_description
        buffer.input_query = input_query_description
        buffer.input_body = input_body_description
        buffer.input_headers = input_headers_description
        buffer.input_forms = input_forms_description
        buffer.output_headers = output_headers_description
        buffer.output_body = output_body_description

        with pytest.raises(AlreadyDecoratedException):
            buffer.input_path = input_path_description

        with pytest.raises(AlreadyDecoratedException):
            buffer.input_query = input_query_description

        with pytest.raises(AlreadyDecoratedException):
            buffer.input_body = input_body_description

        with pytest.raises(AlreadyDecoratedException):
            buffer.input_headers = input_headers_description

        with pytest.raises(AlreadyDecoratedException):
            buffer.input_forms = input_forms_description

        with pytest.raises(AlreadyDecoratedException):
            buffer.output_headers = output_headers_description

        with pytest.raises(AlreadyDecoratedException):
            buffer.output_body = output_body_description
