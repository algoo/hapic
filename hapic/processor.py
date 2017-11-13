# -*- coding: utf-8 -*-
import typing

from multidict import MultiDict

from hapic.exception import OutputValidationException
from hapic.exception import ConfigurationException


class RequestParameters(object):
    def __init__(
        self,
        path_parameters: dict,
        query_parameters: MultiDict,
        body_parameters: dict,
        form_parameters: MultiDict,
        header_parameters: dict,
        files_parameters: dict,
    ):
        """
        :param path_parameters: Parameters found in path, example:
            (for '/users/<user_id>') '/users/42' =>{'user_id': '42'}

        :param query_parameters: Parameters found in query, example:
            '/foo?group_id=1&group_id=2&deleted=false' => MultiDict(
                (
                    ('group_id', '1'),
                    ('group_id', '2'),
                    ('deleted', 'false'),
                )
            )

        :param body_parameters: Body content in dict format, example:
            JSON body '{"user": {"name":"bob"}}' => {'user': {'name':'bob'}}

        :param form_parameters: Form parameters, example:
            <input type="text" name="name" value="bob"/> => {'name': 'bob'}

        :param header_parameters: headers in dict format, example:
            Connection: keep-alive
            Content-Type: text/plain => {
                                            'Connection': 'keep-alive',
                                            'Content-Type': 'text/plain',
                                        }

        :param files_parameters: TODO BS 20171113: Specify type of file
        storage ?
        """
        self.path_parameters = path_parameters
        self.query_parameters = query_parameters
        self.body_parameters = body_parameters
        self.form_parameters = form_parameters
        self.header_parameters = header_parameters
        self.files_parameters = files_parameters


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
        self._schema = None

    @property
    def schema(self):
        if not self._schema:
            raise ConfigurationException('Schema not set for processor {}'.format(str(self)))
        return self._schema

    @schema.setter
    def schema(self, schema):
        self._schema = schema

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


class MarshmallowInputFilesProcessor(MarshmallowInputProcessor):
    def process(self, data: dict):
        clean_data = self.clean_data(data)
        unmarshall = self.schema.load(clean_data)
        additional_errors = self._get_files_errors(unmarshall.data)

        if unmarshall.errors:
            raise OutputValidationException(
                'Error when validate ouput: {}'.format(
                    str(unmarshall.errors),
                )
            )

        if additional_errors:
            raise OutputValidationException(
                'Error when validate ouput: {}'.format(
                    str(additional_errors),
                )
            )

        return unmarshall.data

    def get_validation_error(self, data: dict) -> ProcessValidationError:
        clean_data = self.clean_data(data)
        unmarshall = self.schema.load(clean_data)
        marshmallow_errors = unmarshall.errors
        additional_errors = self._get_files_errors(unmarshall.data)

        if marshmallow_errors:
            return ProcessValidationError(
                message='Validation error of input data',
                details=marshmallow_errors,
            )

        if additional_errors:
            return ProcessValidationError(
                message='Validation error of input data',
                details=additional_errors,
            )

    def _get_files_errors(self, validated_data: dict) -> typing.Dict[str, str]:
        """
        Additional check of data
        :param validated_data: previously validated data by marshmallow schema
        :return: list of error if any
        """
        errors = {}

        for field_name, field in self.schema.fields.items():
            # Actually just check if value not empty
            # TODO BS 20171102: Think about case where test file content is more complicated
            if field.required and (field_name not in validated_data or not validated_data[field_name]):
                errors.setdefault(field_name, []).append('Missing data for required field')

        return errors
