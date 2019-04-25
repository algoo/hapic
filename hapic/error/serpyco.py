# coding: utf-8
import dataclasses
import typing

from hapic.error.main import DefaultErrorBuilder
from hapic.processor.main import ProcessValidationError
from hapic.type import TYPE_SCHEMA


@dataclasses.dataclass
class DefaultErrorSchema(object):
    message: str
    details: typing.Dict[str, typing.Any] = dataclasses.field(default_factory=lambda: {})
    code: typing.Any = dataclasses.field(default=None)


class SerpycoDefaultErrorBuilder(DefaultErrorBuilder):
    def get_schema(self) -> TYPE_SCHEMA:
        return DefaultErrorSchema

    def build_from_exception(
        self, exception: Exception, include_traceback: bool = False
    ) -> DefaultErrorSchema:
        """
        See hapic.error.ErrorBuilderInterface#build_from_exception docstring
        """
        error_dict = super().build_from_exception(exception, include_traceback)
        return DefaultErrorSchema(
            message=error_dict["message"], details=error_dict["details"], code=error_dict["code"]
        )

    def build_from_validation_error(self, error: ProcessValidationError) -> DefaultErrorSchema:
        """
        See hapic.error.ErrorBuilderInterface#build_from_validation_error
        docstring
        """
        error_dict = super().build_from_validation_error(error)
        return DefaultErrorSchema(
            message=error_dict["message"], details=error_dict["details"], code=error_dict["code"]
        )
