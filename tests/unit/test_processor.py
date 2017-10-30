# -*- coding: utf-8 -*-
import marshmallow as marshmallow
import pytest

from hapic.exception import OutputValidationException
from hapic.processor import MarshmallowOutputProcessor
from hapic.processor import MarshmallowInputProcessor
from tests.base import Base


class MySchema(marshmallow.Schema):
    first_name = marshmallow.fields.String(required=True)
    last_name = marshmallow.fields.String(missing='Doe')


class TestProcessor(Base):
    def test_unit__marshmallow_output_processor__ok__process_success(self):
        processor = MarshmallowOutputProcessor()
        processor.schema = MySchema()

        tested_data = {
            'first_name': 'Alan',
            'last_name': 'Turing',
        }
        data = processor.process(tested_data)

        assert data == tested_data

    def test_unit__marshmallow_output_processor__ok__missing_data(self):
        processor = MarshmallowOutputProcessor()
        processor.schema = MySchema()

        tested_data = {
            'last_name': 'Turing',
        }

        with pytest.raises(OutputValidationException):
            processor.process(tested_data)

    def test_unit__marshmallow_input_processor__ok__process_success(self):
        processor = MarshmallowInputProcessor()
        processor.schema = MySchema()

        tested_data = {
            'first_name': 'Alan',
            'last_name': 'Turing',
        }
        data = processor.process(tested_data)

        assert data == tested_data

    def test_unit__marshmallow_input_processor__error__validation_error(self):
        processor = MarshmallowInputProcessor()
        processor.schema = MySchema()

        tested_data = {
            # Missing 'first_name' key
            'last_name': 'Turing',
        }

        with pytest.raises(OutputValidationException):
            processor.process(tested_data)

        errors = processor.get_validation_error(tested_data)
        assert errors.details
        assert 'first_name' in errors.details

    def test_unit__marshmallow_input_processor__error__validation_error_no_data(self):  # nopep8
        processor = MarshmallowInputProcessor()
        processor.schema = MySchema()

        # Schema will not valid it because require first_name field
        tested_data = {}

        with pytest.raises(OutputValidationException):
            processor.process(tested_data)

        errors = processor.get_validation_error(tested_data)
        assert errors.details
        assert 'first_name' in errors.details

    def test_unit__marshmallow_input_processor__error__validation_error_no_data_none(self):  # nopep8
        processor = MarshmallowInputProcessor()
        processor.schema = MySchema()

        # Schema will not valid it because require first_name field
        tested_data = None

        with pytest.raises(OutputValidationException):
            processor.process(tested_data)

        errors = processor.get_validation_error(tested_data)
        assert errors.details
        assert 'first_name' in errors.details

    def test_unit__marshmallow_input_processor__error__validation_error_no_data_empty_string(self):  # nopep8
        processor = MarshmallowInputProcessor()
        processor.schema = MySchema()

        # Schema will not valid it because require first_name field
        tested_data = ''

        with pytest.raises(OutputValidationException):
            processor.process(tested_data)

        errors = processor.get_validation_error(tested_data)
        assert errors.details
        assert {'_schema': ['Invalid input type.']} == errors.details

    def test_unit__marshmallow_input_processor__ok__completed_data(self):
        processor = MarshmallowInputProcessor()
        processor.schema = MySchema()

        tested_data = {
            'first_name': 'Alan',
        }

        data = processor.process(tested_data)
        assert {
            'first_name': 'Alan',
            'last_name': 'Doe',
        } == data
