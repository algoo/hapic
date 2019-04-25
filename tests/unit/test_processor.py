# -*- coding: utf-8 -*-
from datetime import datetime
from io import BytesIO
import os

from PIL import Image
import marshmallow as marshmallow
import pytest

from hapic.data import HapicFile
from hapic.exception import ProcessException
from hapic.exception import ValidationException
from hapic.processor.marshmallow import MarshmallowProcessor
from tests.base import Base


class MySchema(marshmallow.Schema):
    first_name = marshmallow.fields.String(required=True)
    last_name = marshmallow.fields.String(missing="Doe")


class TestProcessor(Base):
    def test_unit_file_output_processor_ok__process_success_filepath(self):
        processor = MarshmallowProcessor()

        tested_data = HapicFile(file_path=os.path.abspath(__file__))
        data = processor.dump_output_file(tested_data)
        assert data == tested_data

    def test_unit_file_output_processor_ok__process_success_fileobject_as_stream(self):
        processor = MarshmallowProcessor()
        file = BytesIO()
        image = Image.new("RGBA", size=(1000, 1000), color=(0, 0, 0))
        image.save(file, "png")
        file.name = "test_image.png"
        file.seek(0)
        tested_data = HapicFile(file_object=file, mimetype="image/png")
        data = processor.dump_output_file(tested_data)
        assert data == tested_data

    def test_unit_file_output_processor_ok__process_success_fileobject_as_sized_file(self):
        processor = MarshmallowProcessor()
        file = BytesIO()
        image = Image.new("RGBA", size=(1000, 1000), color=(0, 0, 0))
        image.save(file, "png")
        file.name = "test_image.png"
        file.seek(0)
        tested_data = HapicFile(
            file_object=file,
            mimetype="image/png",
            content_length=file.getbuffer().nbytes,
            last_modified=datetime.utcnow(),
        )
        data = processor.dump_output_file(tested_data)
        assert data == tested_data

    def test_unit_file_output_processor__err__bad_last_modified_type(self):
        processor = MarshmallowProcessor()
        file = BytesIO()
        image = Image.new("RGBA", size=(1000, 1000), color=(0, 0, 0))
        image.save(file, "png")
        file.name = "test_image.png"
        file.seek(0)
        tested_data = HapicFile(
            file_object=file, mimetype="image/png", last_modified="uncorrect_type"
        )
        with pytest.raises(ValidationException):
            processor.dump_output_file(tested_data)

    def test_unit_file_output_processor__err__bad_content_length_type(self):
        processor = MarshmallowProcessor()
        file = BytesIO()
        image = Image.new("RGBA", size=(1000, 1000), color=(0, 0, 0))
        image.save(file, "png")
        file.name = "test_image.png"
        file.seek(0)
        tested_data = HapicFile(
            file_object=file, mimetype="image/png", content_length="uncorrect_type"
        )
        with pytest.raises(ValidationException):
            processor.dump_output_file(tested_data)

    def test_unit_file_output_processor__err__negative_content_length(self):
        processor = MarshmallowProcessor()
        file = BytesIO()
        image = Image.new("RGBA", size=(1000, 1000), color=(0, 0, 0))
        image.save(file, "png")
        file.name = "test_image.png"
        file.seek(0)
        tested_data = HapicFile(file_object=file, mimetype="image/png", content_length=-1)
        with pytest.raises(ValidationException):
            processor.dump_output_file(tested_data)

    def test_unit_file_output_processor_err__wrong_type(self):
        processor = MarshmallowProcessor()
        file = BytesIO()
        image = Image.new("RGBA", size=(1000, 1000), color=(0, 0, 0))
        image.save(file, "png")
        file.name = "test_image.png"
        file.seek(0)
        tested_data = None
        with pytest.raises(ValidationException):
            processor.dump_output_file(tested_data)

    def test_unit_file_output_processor_err__both_path_and_object(self):
        processor = MarshmallowProcessor()
        file = BytesIO()
        image = Image.new("RGBA", size=(1000, 1000), color=(0, 0, 0))
        image.save(file, "png")
        file.name = "test_image.png"
        file.seek(0)
        tested_data = HapicFile(
            file_path=os.path.abspath(__file__), file_object=file, mimetype="image/png"
        )
        with pytest.raises(ValidationException):
            processor.dump_output_file(tested_data)

    def test_unit_file_output_processor_err__no_path_no_object(self):
        processor = MarshmallowProcessor()
        file = BytesIO()
        image = Image.new("RGBA", size=(1000, 1000), color=(0, 0, 0))
        image.save(file, "png")
        file.name = "test_image.png"
        file.seek(0)
        tested_data = HapicFile(mimetype="image/png")
        with pytest.raises(ValidationException):
            processor.dump_output_file(tested_data)

    def test_unit_file_output_processor_err__file_do_not_exist(self):
        processor = MarshmallowProcessor()
        tested_data = HapicFile(file_path="_____________")
        with pytest.raises(ValidationException):
            processor.dump_output_file(tested_data)

    def test_unit_file_output_processor_err__missing_mimetype_for_file_object(self):
        processor = MarshmallowProcessor()
        file = BytesIO()
        image = Image.new("RGBA", size=(1000, 1000), color=(0, 0, 0))
        image.save(file, "png")
        file.name = "test_image.png"
        file.seek(0)
        tested_data = HapicFile(file_object=file)
        with pytest.raises(ValidationException):
            processor.dump_output_file(tested_data)

    def test_unit__marshmallow_output_processor__ok__process_success(self):
        processor = MarshmallowProcessor()
        processor.set_schema(MySchema())

        tested_data = {"first_name": "Alan", "last_name": "Turing"}
        data = processor.dump(tested_data)

        assert data == tested_data

    def test_unit__marshmallow_output_processor__ok__missing_data(self):
        processor = MarshmallowProcessor()
        processor.set_schema(MySchema())

        tested_data = {"last_name": "Turing"}

        with pytest.raises(ValidationException):
            processor.dump(tested_data)

    def test_unit__marshmallow_input_processor__ok__process_success(self):
        processor = MarshmallowProcessor()
        processor.set_schema(MySchema())

        tested_data = {"first_name": "Alan", "last_name": "Turing"}
        data = processor.load(tested_data)

        assert data == tested_data

    def test_unit__marshmallow_input_processor__error__validation_error(self):
        processor = MarshmallowProcessor()
        processor.set_schema(MySchema())

        tested_data = {
            # Missing 'first_name' key
            "last_name": "Turing"
        }

        with pytest.raises(ValidationException):
            processor.load(tested_data)

        errors = processor.get_input_validation_error(tested_data)
        assert errors.details
        assert "first_name" in errors.details

    def test_unit__marshmallow_input_processor__error__validation_error_no_data(self):
        processor = MarshmallowProcessor()
        processor.set_schema(MySchema())

        # Schema will not valid it because require first_name field
        tested_data = {}

        with pytest.raises(ValidationException):
            processor.load(tested_data)

        errors = processor.get_input_validation_error(tested_data)
        assert errors.details
        assert "first_name" in errors.details

    def test_unit__marshmallow_input_processor__error__validation_error_no_data_none(self):
        processor = MarshmallowProcessor()
        processor.set_schema(MySchema())

        # Schema will not valid it because require first_name field
        tested_data = None

        with pytest.raises(ValidationException):
            processor.load(tested_data)

        errors = processor.get_input_validation_error(tested_data)
        assert errors.details
        assert "first_name" in errors.details

    def test_unit__marshmallow_input_processor__error__validation_error_no_data_empty_string(self):
        processor = MarshmallowProcessor()
        processor.set_schema(MySchema())

        # Schema will not valid it because require first_name field
        tested_data = ""

        with pytest.raises(ProcessException):
            processor.load(tested_data)

        errors = processor.get_input_validation_error(tested_data)
        assert errors.details
        assert {"_schema": ["Invalid input type."]} == errors.details

    def test_unit__marshmallow_input_processor__ok__completed_data(self):
        processor = MarshmallowProcessor()
        processor.set_schema(MySchema())

        tested_data = {"first_name": "Alan"}

        data = processor.load(tested_data)
        assert {"first_name": "Alan", "last_name": "Doe"} == data
