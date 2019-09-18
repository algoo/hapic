import typing

from apispec import BasePlugin
from apispec_marshmallow_advanced import MarshmallowAdvancedPlugin
from apispec_marshmallow_advanced.common import generate_schema_name
from apispec_marshmallow_advanced.common import schema_class_resolver as schema_class_resolver_

from hapic.doc.schema import SchemaUsage
from hapic.error.main import ErrorBuilderInterface
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
from hapic.exception import OutputValidationException
from hapic.exception import ValidationException
from hapic.processor.main import Processor
from hapic.processor.main import ProcessValidationError


class MarshmallowProcessor(Processor):
    """
    Marshmallow implementation of Processor
    """

    @classmethod
    def create_apispec_plugin(
        cls, schema_name_resolver: typing.Optional[typing.Callable] = None
    ) -> BasePlugin:
        schema_name_resolver = schema_name_resolver or generate_schema_name

        return MarshmallowAdvancedPlugin(schema_name_resolver=schema_name_resolver)

    def generate_schema_ref(self, main_plugin: MarshmallowAdvancedPlugin) -> dict:
        """
        Return OpenApi $ref in a dict,
        eg. {"$ref": "#/definitions/MySchema"} or
            {'type': 'array', 'items': {"$ref": "#/definitions/MySchema"}}
        """
        schema_class = schema_class_resolver_(main_plugin, self.schema)
        ref = {"$ref": "#/definitions/{}".format(main_plugin.schema_name_resolver(schema_class))}

        if self.schema.many:
            return {"type": "array", "items": ref}

        return ref

    def schema_class_resolver(self, main_plugin: MarshmallowAdvancedPlugin) -> SchemaUsage:
        """
        Return schema class with adaptation if needed.
        :param main_plugin: Apispec plugin associated for marshmallow
        :return: schema generated from given schema or original schema if
            no change required.
        """
        return SchemaUsage(schema_class_resolver_(main_plugin, self.schema))

    def clean_data(self, data: typing.Any) -> dict:
        """
        Transform data in readable data for processor itself.
        :param data:
        :return:
        """
        # Fixes #22: Schemas make not validation if None is given
        if data is None:
            return {}
        return data

    def get_input_validation_error(self, data_to_validate: typing.Any) -> ProcessValidationError:
        """
        Return ProcessValidationError for given input data
        :param data_to_validate: data used to produce ProcessValidationError
        :return: ProcessValidationError instance for given data
        """
        clean_data = self.clean_data(data_to_validate)
        marshmallow_errors = self.schema.load(clean_data).errors

        return ProcessValidationError(
            message="Validation error of input data", details=marshmallow_errors
        )

    def get_input_files_validation_error(
        self, data_to_validate: typing.Any
    ) -> ProcessValidationError:
        """
        Return a ProcessValidationError about files for given data
        :param data_to_validate: data containing files
        :return: ProcessValidationError instance for given data files
        """
        clean_data = self.clean_data(data_to_validate)
        unmarshall = self.schema.load(clean_data)
        errors = unmarshall.errors
        additional_errors = self._get_input_files_errors(unmarshall.data)
        errors.update(additional_errors)

        return ProcessValidationError(message="Validation error of input data", details=errors)

    def get_output_validation_error(self, data_to_validate: typing.Any) -> ProcessValidationError:
        """
        Return ProcessValidationError for given output data
        :param data_to_validate: output data to use
        :return: ProcessValidationError instance for given output data
        """
        clean_data = self.clean_data(data_to_validate)
        dump_data = self.schema.dump(clean_data).data
        errors = self.schema.load(dump_data).errors

        return ProcessValidationError(message="Validation error of output data", details=errors)

    def get_output_file_validation_error(
        self, data_to_validate: typing.Any
    ) -> ProcessValidationError:
        """
        Return a ProcessValidationError for given output file
        :param data_to_validate: output file
        :return: ProcessValidationError instance for given output file
        """
        validation_error_message = self._get_ouput_file_validation_error_message(data_to_validate)

        return ProcessValidationError(
            message="Validation error of output file",
            details={"output_file": validation_error_message},
        )

    def load(self, data: typing.Any) -> typing.Any:
        """
        Use schema to validate given data and return updated data (like
        with default values).
        If validation fail, raise InputValidationException
        :param data: data to validate and process
        :return: updated data (like with default values)
        """
        clean_data = self.clean_data(data)
        unmarshall = self.schema.load(clean_data)
        if unmarshall.errors:
            raise ValidationException("Error when loading: {}".format(str(unmarshall.errors)))

        return unmarshall.data

    def dump(self, data: typing.Any) -> typing.Any:
        """
        Use schema to validate given data and return dumped data.
        If validation fail, raise InputValidationException
        :param data: data to validate and dump
        :return: dumped data
        """
        clean_data = self.clean_data(data)
        dump_data = self.schema.dump(clean_data).data

        # Re-validate with dumped data
        errors = self.schema.load(dump_data).errors
        if errors:
            raise ValidationException("Error when dumping: {}".format(str(errors)))

        return dump_data

    def load_files_input(self, input_data: typing.Any) -> typing.Any:
        """
        Validate input files and raise OutputValidationException if validation errors.
        :param input_data: input data containing files
        :return:
        """
        clean_data = self.clean_data(input_data)
        unmarshall = self.schema.load(clean_data)
        additional_errors = self._get_input_files_errors(unmarshall.data)

        if unmarshall.errors or additional_errors:
            raise OutputValidationException(
                "Error when validate ouput: {}".format(
                    ", ".join([str(unmarshall.errors), str(additional_errors)])
                )
            )

        return unmarshall.data

    def _get_input_files_errors(self, validated_data: dict) -> typing.Dict[str, str]:
        """
        Additional check of data
        :param validated_data: previously validated data by marshmallow schema
        :return: list of error if any
        """
        errors = {}

        for field_name, field in self.schema.fields.items():
            # Currenlty just check if value not empty
            # TODO BS 20171102: Think about case where test file content is
            # more complicated
            if field.required and (
                field_name not in validated_data or not validated_data[field_name]
            ):
                errors.setdefault(field_name, []).append("Missing data for required field")

        return errors

    def dump_output(self, output_data: typing.Any) -> typing.Union[typing.Dict, typing.List]:
        """
        Dump output data and raise OutputValidationException if validation error
        :param output_data: output data to validate
        :return: given data
        """
        clean_data = self.clean_data(output_data)
        dump_data = self.schema.dump(clean_data).data

        # Validate
        errors = self.schema.load(dump_data).errors
        if errors:
            raise OutputValidationException("Error when validate input: {}".format(str(errors)))

        return dump_data

    def dump_output_file(self, output_file: typing.Any) -> typing.Any:
        """
        Must validate view output (expected) file.
        :param output_file: (expected) output file from view
        :return: Hapic compatible file object (Processable by
            used context.get_file_response method)
        """
        self._validate_output_file(output_file)
        return output_file

    def _validate_output_file(self, data: typing.Any) -> None:
        """
        Raise OutputValidationException if given object cannot be accepted as file
        :param data: object to be check as acceptable file
        """
        validation_error_message = self._get_ouput_file_validation_error_message(data)
        if validation_error_message:
            raise OutputValidationException(
                "Error when validate output file : {}".format(validation_error_message)
            )

    @classmethod
    def get_default_error_builder(cls) -> ErrorBuilderInterface:
        """
        :return: Default error builder to use for this processor
        """
        return MarshmallowDefaultErrorBuilder()
