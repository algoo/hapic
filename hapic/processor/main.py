import abc
import os
import typing

from apispec import BasePlugin
from multidict.__init__ import MultiDict

from hapic.data import HapicFile
from hapic.exception import ConfigurationException

if typing.TYPE_CHECKING:
    from hapic.hapic import TYPE_SCHEMA


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


class Processor(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        self._schema = None  # type: typing.Any

    def set_schema(self, schema: typing.Any) -> None:
        """
        Set schema who will be used in validation, dump or load process
        :param schema: schema object useable by the processor
        """
        self._schema = schema

    @classmethod
    @abc.abstractmethod
    def create_apispec_plugin(
        cls,
        schema_name_resolver: typing.Optional[typing.Callable] = None,
    ) -> BasePlugin:
        """
        Must return instance of matching apispec plugin to use for generate
        OpenAPI documentation.
        """

    @classmethod
    @abc.abstractmethod
    def generate_schema_ref(
        cls,
        main_plugin: BasePlugin,
        schema: 'TYPE_SCHEMA',
    ) -> dict:
        """
        Must return OpenApi $ref in a dict,
        eg. {"$ref": "#/definitions/MySchema"}
        """

    @classmethod
    def schema_class_resolver(
        cls,
        main_plugin: BasePlugin,
        schema: 'TYPE_SCHEMA',
    ) -> 'TYPE_SCHEMA':
        """
        Return schema class with adaptation if needed.
        :param main_plugin: associated Apispec plugin
        :param schema: schema to proceed
        :return: schema generated from given schema or original schema if
            no change required.
        """
        return schema

    @property
    def schema(self):
        if not self._schema:
            raise ConfigurationException(
                'Schema not set for processor {}'.format(str(self))
            )
        return self._schema

    @abc.abstractmethod
    def clean_data(self, raw_data: typing.Any) -> dict:
        """
        Transform data in readable data for processor itself.
        :param raw_data: data received from view response
        :return: ready to be processed data
        """

    @abc.abstractmethod
    def get_input_validation_error(
        self,
        data_to_validate: typing.Any,
    ) -> ProcessValidationError:
        """
        Must return an ProcessValidationError containing validation
        detail error for input data
        """

    @abc.abstractmethod
    def get_input_files_validation_error(
        self,
        data_to_validate: typing.Any,
    ) -> ProcessValidationError:
        """
        Must return an ProcessValidationError containing validation
        detail error for input data files
        """

    @abc.abstractmethod
    def get_output_validation_error(
        self,
        data_to_validate: typing.Any,
    ) -> ProcessValidationError:
        """
        Must return an ProcessValidationError containing validation
        detail error for output data
        """

    @abc.abstractmethod
    def get_output_file_validation_error(
        self,
        data_to_validate: typing.Any,
    ) -> ProcessValidationError:
        """
        Must return an ProcessValidationError containing validation
        detail error for output file data
        """

    @abc.abstractmethod
    def load_input(self, input_data: typing.Any) -> typing.Any:
        """
        Must use schema to validate an load input data.
        Raise ProcessValidationError in case of validation error
        :param input_data: input data to validate and update to give to view
        :return: updated data (like with default values)
        """

    @abc.abstractmethod
    def load_files_input(self, input_data: typing.Any) -> typing.Any:
        """
        Must use schema to validate an load input data files.
        Raise ProcessValidationError in case of validation error
        :param input_data: input data to validate and update to give to view
        :return: original data if ok
        """

    @abc.abstractmethod
    def dump_output(
        self,
        output_data: typing.Any,
    ) -> typing.Union[typing.Dict, typing.List]:
        """
        Must use schema to validate an dump output data.
        Raise ProcessValidationError in case of validation error
        :param output_data: output data got from view
        :return: dumped data
        """

    @abc.abstractmethod
    def dump_output_file(
        self,
        output_file: typing.Any,
    ) -> typing.Any:
        """
        Must validate view output (expected) file.
        :param output_file: (expected) output file from view
        :return: Hapic compatible file object (Processable by
            used context.get_file_response method)
        """

    def _get_ouput_file_validation_error_message(self, data: typing.Any) -> typing.Optional[str]:
        """
        Return a specific error message for given object
        :param data: object to be processed as file
        :return:
        """
        error_message = None
        if not isinstance(data, HapicFile):
            error_message = 'File should be HapicFile type'
        elif data.file_path and data.file_object:
            error_message = 'File should be either path or object, not both'
        elif not data.file_path and not data.file_object:
            error_message = 'File should be either path or object'
        elif data.file_path and not os.path.isfile(data.file_path):
            error_message = 'File path is not correct, file do not exist'
        elif data.file_object and not data.mimetype:
            error_message = 'File object should have explicit mimetype'
        return error_message
