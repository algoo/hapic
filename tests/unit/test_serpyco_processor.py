# coding: utf-8
import dataclasses
import typing

import pytest

from hapic.exception import OutputValidationException
from hapic.processor.serpyco import SerpycoProcessor

from tests.base import Base


@pytest.fixture
def serpyco_processor() -> SerpycoProcessor:
    yield SerpycoProcessor()


@dataclasses.dataclass
class OneFileSchema:
    file1: typing.Any


@dataclasses.dataclass
class TwoFileSchema:
    file1: typing.Any
    file2: typing.Any


class TestSerpycoProcessor(Base):
    def test_unit__get_input_files_validation_error__ok__missing_one_file(
        self, serpyco_processor: SerpycoProcessor
    ) -> None:
        serpyco_processor.set_schema(OneFileSchema)
        error = serpyco_processor.get_input_files_validation_error({})

        assert {'file1': 'data is missing'} == error.details
        assert 'Validation error of input data' == error.message

    def test_unit__get_input_files_validation_error__ok__missing_two_file(
        self, serpyco_processor: SerpycoProcessor
    ) -> None:
        serpyco_processor.set_schema(TwoFileSchema)
        error = serpyco_processor.get_input_files_validation_error({})

        assert {'file1': 'data is missing', 'file2': 'data is missing'} == error.details
        assert 'Validation error of input data' == error.message

    def test_unit__load_files_input__ok__one_file(
        self, serpyco_processor: SerpycoProcessor
    ) -> None:
        serpyco_processor.set_schema(OneFileSchema)
        input_data = serpyco_processor.load_files_input({"file1": b"42"})

        assert isinstance(input_data, OneFileSchema)
        assert b"42" == input_data.file1

    def test_unit__load_files_input__ok__two_file(
        self, serpyco_processor: SerpycoProcessor
    ) -> None:
        serpyco_processor.set_schema(TwoFileSchema)
        input_data = serpyco_processor.load_files_input({"file1": b"42", "file2": b"43"})

        assert isinstance(input_data, TwoFileSchema)
        assert b"42" == input_data.file1
        assert b"43" == input_data.file2

    def test_unit__load_files_input__error__no_file_given(
        self, serpyco_processor: SerpycoProcessor
    ) -> None:
        serpyco_processor.set_schema(OneFileSchema)

        with pytest.raises(OutputValidationException):
            serpyco_processor.load_files_input({})

    def test_unit__load_files_input__error__none_file_given(
        self, serpyco_processor: SerpycoProcessor
    ) -> None:
        serpyco_processor.set_schema(OneFileSchema)

        with pytest.raises(OutputValidationException):
            serpyco_processor.load_files_input({"file1": None})
