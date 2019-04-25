# -*- coding: utf-8 -*-
import abc
import traceback
import typing

from hapic.processor.main import ProcessValidationError
from hapic.type import TYPE_SCHEMA


class ErrorBuilderInterface(metaclass=abc.ABCMeta):
    """
    ErrorBuilder is a class who represent a Schema (marshmallow.Schema) and
    can generate a response content from exception (build_from_exception)
    """

    @abc.abstractmethod
    def build_from_exception(
        self, exception: Exception, include_traceback: bool = False
    ) -> typing.Any:
        """
        Build the error response content from given exception
        :param include_traceback: if True, error response must include
            exception traceback
        :param exception: Original exception who invoke this method
        :return: object representing the error response content: this object
            must be useable by processor
        """

    @abc.abstractmethod
    def build_from_validation_error(self, error: ProcessValidationError) -> typing.Any:
        """
        Build the error response content from given process validation error
        :param error: Original ProcessValidationError who invoke this method
        :return: object representing the error response content: this object
            must be useable by processor
        """

    @abc.abstractmethod
    def get_schema(self) -> TYPE_SCHEMA:
        """
        Must return schema of produced errors
        """


class DefaultErrorBuilder(ErrorBuilderInterface):
    def build_from_exception(self, exception: Exception, include_traceback: bool = False) -> dict:
        """
        See hapic.error.ErrorBuilderInterface#build_from_exception docstring
        """
        # TODO: "error_detail" attribute name should be configurable
        message = str(exception)
        if not message:
            message = type(exception).__name__

        details = {"error_detail": getattr(exception, "error_detail", {})}
        if include_traceback:
            details["traceback"] = traceback.format_exc()

        return {"message": message, "details": details, "code": None}

    def build_from_validation_error(self, error: ProcessValidationError) -> dict:
        """
        See hapic.error.ErrorBuilderInterface#build_from_validation_error
        docstring
        """
        return {"message": error.message, "details": error.details, "code": None}

    @abc.abstractmethod
    def get_schema(self) -> TYPE_SCHEMA:
        """
        Must return schema of produced errors
        """
