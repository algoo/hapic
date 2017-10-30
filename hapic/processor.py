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
        message: str,
        details: dict,
    ) -> None:
        self.message = message
        self.details = details


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


class Processor(ProcessorInterface):
    @classmethod
    def clean_data(cls, data: typing.Any) -> dict:
        # Fixes #22: Schemas make not validation if None is given
        if data is None:
            return {}
        return data


class InputProcessor(Processor):
    pass


class OutputProcessor(Processor):
    pass


class MarshmallowOutputProcessor(OutputProcessor):
    def process(self, data: typing.Any):
        clean_data = self.clean_data(data)
        dump_data = self.schema.dump(clean_data).data
        self.validate(dump_data)
        return dump_data

    def validate(self, data: typing.Any) -> None:
        clean_data = self.clean_data(data)
        errors = self.schema.load(clean_data).errors
        if errors:
            raise OutputValidationException(
                'Error when validate input: {}'.format(
                    str(errors),
                )
            )

    def get_validation_error(self, data: dict) -> ProcessValidationError:
        clean_data = self.clean_data(data)
        dump_data = self.schema.dump(clean_data).data
        errors = self.schema.load(dump_data).errors
        return ProcessValidationError(
            message='Validation error of output data',
            details=errors,
        )


class MarshmallowInputProcessor(InputProcessor):
    def process(self, data: dict):
        clean_data = self.clean_data(data)
        unmarshall = self.schema.load(clean_data)
        if unmarshall.errors:
            raise OutputValidationException(
                'Error when validate ouput: {}'.format(
                    str(unmarshall.errors),
                )
            )

        return unmarshall.data

    def get_validation_error(self, data: dict) -> ProcessValidationError:
        clean_data = self.clean_data(data)
        marshmallow_errors = self.schema.load(clean_data).errors
        return ProcessValidationError(
            message='Validation error of input data',
            details=marshmallow_errors,
        )
