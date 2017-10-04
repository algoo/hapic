# -*- coding: utf-8 -*-
import typing

from hapic.exception import InputValidationException, OutputValidationException


class RequestParameters(object):
    def __init__(
        self,
        path_parameters,
        query_parameters,
        body_parameters,
        form_parameters,
        header_parameters,
    ):
        self.path_parameters = path_parameters
        self.query_parameters = query_parameters
        self.body_parameters = body_parameters
        self.form_parameters = form_parameters
        self.header_parameters = header_parameters


class ProcessValidationError(object):
    def __init__(
        self,
        error_message: str,
        error_details: dict,
    ) -> None:
        self.error_message = error_message
        self.error_details = error_details


class ProcessorInterface(object):
    def __init__(self):
        self.schema = None

    def process(self, value):
        raise NotImplementedError

    def get_validation_error(
        self,
        request_context: RequestParameters,
    ) -> ProcessValidationError:
        raise NotImplementedError


class InputProcessor(ProcessorInterface):
    pass


class OutputProcessor(ProcessorInterface):
    pass


class MarshmallowOutputProcessor(OutputProcessor):
    def process(self, data: typing.Any):
        data = self.schema.dump(data).data
        self.validate(data)
        return data

    def validate(self, data: typing.Any) -> None:
        errors = self.schema.load(data).errors
        if errors:
            raise OutputValidationException(
                'Error when validate input: {}'.format(
                    str(errors),
                )
            )

    def get_validation_error(self, data: dict) -> ProcessValidationError:
        data = self.schema.dump(data).data
        errors = self.schema.load(data).errors
        return ProcessValidationError(
            error_message='Validation error of output data',
            error_details=errors,
        )


class MarshmallowInputProcessor(OutputProcessor):
    def process(self, data: dict):
        unmarshall = self.schema.load(data)
        if unmarshall.errors:
            raise OutputValidationException(
                'Error when validate ouput: {}'.format(
                    str(unmarshall.errors),
                )
            )

        return unmarshall.data

    def get_validation_error(self, data: dict) -> ProcessValidationError:
        marshmallow_errors = self.schema.load(data).errors
        return ProcessValidationError(
            error_message='Validation error of input data',
            error_details=marshmallow_errors,
        )

