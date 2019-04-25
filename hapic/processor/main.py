import abc
from datetime import datetime
import os
import typing

from apispec import BasePlugin
from multidict.__init__ import MultiDict

from hapic.data import HapicFile
from hapic.doc.schema import SchemaUsage
from hapic.exception import ConfigurationException

if typing.TYPE_CHECKING:
    from hapic.type import TYPE_SCHEMA  # noqa: F401
    from hapic.error.main import ErrorBuilderInterface


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
        self, message: str, details: dict, original_exception: typing.Optional[Exception] = None
    ) -> None:
        self.message = message
        self.details = details
        self.original_exception = original_exception


class Processor(metaclass=abc.ABCMeta):
    def __init__(self, schema: typing.Optional["TYPE_SCHEMA"] = None) -> None:
        self._schema = schema

    def set_schema(self, schema: typing.Any) -> None:
        """
        Set schema who will be used in validation, dump or load process
        :param schema: schema object useable by the processor
        """
        self._schema = schema

    @classmethod
    @abc.abstractmethod
    def create_apispec_plugin(
        cls, schema_name_resolver: typing.Optional[typing.Callable] = None
    ) -> BasePlugin:
        """
        Must return instance of matching apispec plugin to use for generate
        OpenAPI documentation.
        """

    @abc.abstractmethod
    def generate_schema_ref(self, main_plugin: BasePlugin) -> dict:
        """
        Must return OpenApi $ref in a dict,
        eg. {"$ref": "#/definitions/MySchema"}
        """

    def schema_class_resolver(self, main_plugin: BasePlugin) -> SchemaUsage:
        """
        Return schema class with adaptation if needed.
        :param main_plugin: associated Apispec plugin
        :return: SchemaUsage containing schema generated from
        given schema or original schema if no change required and optional
        apispec plugin kwargs for json_schema generation.
        """
        return SchemaUsage(self.schema)

    @property
    def schema(self):
        if not self._schema:
            raise ConfigurationException("Schema not set for processor {}".format(str(self)))
        return self._schema

    @abc.abstractmethod
    def clean_data(self, raw_data: typing.Any) -> dict:
        """
        Transform data in readable data for processor itself.
        :param raw_data: data received from view response
        :return: ready to be processed data
        """

    @abc.abstractmethod
    def get_input_validation_error(self, data_to_validate: typing.Any) -> ProcessValidationError:
        """
        Must return an ProcessValidationError containing validation
        detail error for input data
        """

    @abc.abstractmethod
    def get_input_files_validation_error(
        self, data_to_validate: typing.Any
    ) -> ProcessValidationError:
        """
        Must return an ProcessValidationError containing validation
        detail error for input data files
        """

    @abc.abstractmethod
    def get_output_validation_error(self, data_to_validate: typing.Any) -> ProcessValidationError:
        """
        Must return an ProcessValidationError containing validation
        detail error for output data
        """

    @abc.abstractmethod
    def get_output_file_validation_error(
        self, data_to_validate: typing.Any
    ) -> ProcessValidationError:
        """
        Must return an ProcessValidationError containing validation
        detail error for output file data
        """

    @abc.abstractmethod
    def load(self, data: typing.Any) -> typing.Any:
        """
        Must use schema to validate given data and return updated data (like
        with default values).
        If validation fail, must raise InputValidationException
        :param data: data to validate and process
        :return: updated data (like with default values)
        """

    @abc.abstractmethod
    def dump(self, data: typing.Any) -> typing.Any:
        """
        Must use schema to validate given data and return dumped data.
        If validation fail, must raise InputValidationException
        :param data: data to validate and dump
        :return: dumped data
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
    def dump_output_file(self, output_file: typing.Any) -> typing.Any:
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
            error_message = "File should be HapicFile type"
        elif data.file_path and data.file_object:
            error_message = "File should be either path or object, not both"
        elif not data.file_path and not data.file_object:
            error_message = "File should be either path or object"
        elif data.file_path and not os.path.isfile(data.file_path):
            error_message = "File path is not correct, file do not exist"
        elif data.file_object and not data.mimetype:
            error_message = "File object should have explicit mimetype"
        elif data.content_length and not isinstance(data.content_length, int):
            error_message = "Content length should be integer"
        elif data.content_length and data.content_length < 0:
            error_message = "Content length should positive or null integer"
        elif data.last_modified and not isinstance(data.last_modified, datetime):
            error_message = "Last-modified value should be datetime type"
        return error_message

    # NOTE BS 2018-12-20: the decorators order is not semantically right,
    # but in right order pycharm generates a warning: "This decorator will not receive a callable
    # it may expect; the built-in decorator returns a special object"
    @classmethod
    @abc.abstractmethod
    def get_default_error_builder(cls) -> "ErrorBuilderInterface":
        """
        :return: Default error builder to use for this processor
        """
