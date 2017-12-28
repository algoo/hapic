# -*- coding: utf-8 -*-
import marshmallow

from hapic.processor import ProcessValidationError


class ErrorBuilderInterface(marshmallow.Schema):
    """
    ErrorBuilder is a class who represent a Schema (marshmallow.Schema) and
    can generate a response content from exception (build_from_exception)
    """
    def build_from_exception(self, exception: Exception) -> dict:
        """
        Build the error response content from given exception
        :param exception: Original exception who invoke this method
        :return: a dict representing the error response content
        """
        raise NotImplementedError()

    def build_from_validation_error(
        self,
        error: ProcessValidationError,
    ) -> dict:
        """
        Build the error response content from given process validation error
        :param error: Original ProcessValidationError who invoke this method
        :return: a dict representing the error response content
        """
        raise NotImplementedError()


class DefaultErrorBuilder(ErrorBuilderInterface):
    message = marshmallow.fields.String(required=True)
    details = marshmallow.fields.Dict(required=False, missing={})
    code = marshmallow.fields.Raw(missing=None)

    def build_from_exception(self, exception: Exception) -> dict:
        """
        See hapic.error.ErrorBuilderInterface#build_from_exception docstring
        """
        # TODO: "error_detail" attribute name should be configurable
        return {
            'message': str(exception),
            'details': getattr(exception, 'error_detail', {}),
            'code': None,
        }

    def build_from_validation_error(
        self,
        error: ProcessValidationError,
    ) -> dict:
        """
        See hapic.error.ErrorBuilderInterface#build_from_validation_error
        docstring
        """
        return {
            'message': error.message,
            'details': error.details,
            'code': None,
        }
