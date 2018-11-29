import logging
import typing

from apispec import BasePlugin
from apispec_serpyco import SerpycoPlugin
from apispec_serpyco.utils import schema_name_resolver as schema_name_resolver_
from multidict import MultiDictProxy
import serpyco
from serpyco import ValidationError
from serpyco.serializer import Serializer

from hapic.exception import InputValidationException
from hapic.exception import OutputValidationException
from hapic.exception import WorkflowException
from hapic.processor.main import Processor
from hapic.processor.main import ProcessValidationError
from hapic.util import LOGGER_NAME


def exception_to_error_dict(exc: ValidationError) -> dict:
    """
    FIXME BS 2018-11-16: Is there a correct way to structure the
    json_schema errors ?
    :param exc: ValidationError exception to process
    :return: dict with detail of error
    """
    errors = {}

    for err_tuple in exc.args[1:]:
        errors[err_tuple[0]] = (err_tuple[1], err_tuple[2])

    return errors


class SerpycoProcessor(Processor):
    def __init__(
        self,
        only: typing.Optional[typing.List[str]] = None,
        exclude: typing.Optional[typing.List[str]] = None,
        many: bool = False,
    ) -> None:
        super().__init__()
        self._logger = logging.getLogger(LOGGER_NAME)
        self._serializer = None  # type: Serializer
        self._only = only
        self._exclude = exclude
        self._many = many

    @classmethod
    def create_apispec_plugin(
        cls,
        schema_name_resolver: typing.Optional[typing.Callable] = None,
    ) -> BasePlugin:
        schema_name_resolver = schema_name_resolver or schema_name_resolver_
        return SerpycoPlugin(
            schema_name_resolver=schema_name_resolver,
        )

    @classmethod
    def generate_schema_ref(
        cls,
        main_plugin: SerpycoPlugin,
        schema: type,
    ) -> dict:
        """
        Return OpenApi $ref in a dict,
        eg. {"$ref": "#/definitions/MySchema"}
        """
        ref = {
            '$ref': '#/definitions/{}'.format(
                main_plugin.schema_name_resolver(schema)
            )
        }

        return ref

    @property
    def serializer(self) -> Serializer:
        """
        Return cached (create id if not yet created) serializer
        :return: serializer instance
        """
        if self._serializer is None:
            self._serializer = serpyco.Serializer(
                self.schema,
                only=self._only,
                exclude=self._exclude,
                many=self._many,
            )

        return self._serializer

    def clean_data(
        self,
        raw_data: typing.Any,
    ) -> dict:
        """
        Return given data. Update this method if potential "None" value must be adapted fo serpyco
        :param raw_data: raw data from http
        :return: serpyco acceptable data
        """
        return raw_data

    def get_input_validation_error(
        self,
        data_to_validate: typing.Any,
    ) -> ProcessValidationError:
        """
        Return an ProcessValidationError containing validation
        detail error for input data
        :param data_to_validate: data to use to generate validation error
        :return:
        """
        # TODO BS 2018-11-26: This is correct to do this every times ?
        if isinstance(data_to_validate, MultiDictProxy):
            data_to_validate = dict(data_to_validate)

        try:
            self.serializer.load(data_to_validate)
            raise WorkflowException(
                'Serializer should raise an exception here',
            )
        except ValidationError as exc:
            return ProcessValidationError(
                message='Validation error of input data: "{}"'.format(
                    exc.args[0],
                ),
                details=exception_to_error_dict(exc),
            )
        except Exception as exc:
            self._logger.exception(
                'Unknown error during serpyco load: "{}"'.format(
                    str(exc)
                )
            )
            return ProcessValidationError(
                message='Unknown error during validation '
                        'of input data: "{}"'.format(
                            str(exc),
                        ),
                details={},
            )

    def get_input_files_validation_error(
        self,
        data_to_validate: typing.Any,
    ) -> ProcessValidationError:
        # FIXME BS 2018-11-22: code it
        raise NotImplementedError('TODO')

    def get_output_validation_error(
        self,
        data_to_validate: typing.Any,
    ) -> ProcessValidationError:
        """
        Return a ProcessValidationError containing validation
        detail error for output data
        """
        try:
            self.serializer.dump(data_to_validate, validate=True)
            raise WorkflowException(
                'Serializer should raise an exception here',
            )
        except ValidationError as exc:
            return ProcessValidationError(
                message='Validation error of output data: "{}"'.format(
                    exc.args[0],
                ),
                details=exception_to_error_dict(exc),
            )
        except Exception as exc:
            self._logger.exception(
                'Unknown error during serpyco dump: "{}"'.format(
                    str(exc)
                )
            )
            return ProcessValidationError(
                message='Unknown error during validation error '
                        'of output data: "{}"'.format(
                            str(exc),
                        ),
                details={},
            )

    def get_output_file_validation_error(
        self,
        data_to_validate: typing.Any,
    ) -> ProcessValidationError:
        """
        Return an ProcessValidationError containing validation
        detail error for output file data
        """
        validation_error_message = \
            self._get_ouput_file_validation_error_message(data_to_validate)

        return ProcessValidationError(
            message='Validation error of output file',
            details={'output_file': validation_error_message},
        )

    def load_input(
        self,
        input_data: typing.Any,
    ) -> typing.Any:
        """
        Use schema to validate an load input data.
        Raise ProcessValidationError in case of validation error
        :param input_data: input data to validate and update to give to view
        :return: updated data (like with default values)
        """
        # TODO BS 2018-11-26: This is correct to do this every times ?
        if isinstance(input_data, MultiDictProxy):
            input_data = dict(input_data)

        try:
            return self.serializer.load(input_data)
        except ValidationError as exc:
            raise InputValidationException(
                'Error when validate serpyco load: {}'.format(
                    exc.args[0],
                )
            )
        except Exception as exc:
            raise InputValidationException(
                'Unknown error when serpyco load: {}'.format(
                    str(exc),
                )
            )

    def load_files_input(
        self,
        input_data: typing.Any,
    ) -> typing.Any:
        """
        Validate input files and raise OutputValidationException
        if validation errors.
        :param input_data: input data containing files
        :return: original data
        """
        # FIXME BS 2018-11-22: code it
        raise NotImplementedError('TODO')

    def dump_output(
        self,
        output_data: typing.Any,
    ) -> typing.Union[typing.Dict, typing.List]:
        """
        Use schema to validate an dump output data.
        Raise ProcessValidationError in case of validation error
        :param output_data: output data got from view
        :return: dumped data
        """
        try:
            return self.serializer.dump(output_data, validate=True)
        except ValidationError as exc:
            raise OutputValidationException(
                'ValidationError when serpyco dump: {}'.format(
                    exc.args[0],
                )
            )
        except Exception as exc:
            self._logger.exception(
                'Unknown error during serpyco dump: "{}"'.format(
                    str(exc)
                )
            )
            raise OutputValidationException(
                'Unknown error when serpyco dump: {}'.format(
                    str(exc),
                )
            )

    def dump_output_file(
        self,
        output_file: typing.Any,
    ) -> typing.Any:
        """
        Validate view output (expected) file.
        :param output_file: (expected) output file from view
        :return: Hapic compatible file object (Processable by
            used context.get_file_response method)
        """
        # FIXME BS 2018-11-22: code it
        raise NotImplementedError('TODO')
