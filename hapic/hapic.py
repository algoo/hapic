# -*- coding: utf-8 -*-
import typing
import uuid
from http import HTTPStatus
import functools

import marshmallow

from hapic.buffer import DecorationBuffer
from hapic.context import ContextInterface
from hapic.decorator import DecoratedController
from hapic.decorator import DECORATION_ATTRIBUTE_NAME
from hapic.decorator import ControllerReference
from hapic.decorator import ExceptionHandlerControllerWrapper
from hapic.decorator import InputBodyControllerWrapper
from hapic.decorator import InputHeadersControllerWrapper
from hapic.decorator import InputPathControllerWrapper
from hapic.decorator import InputQueryControllerWrapper
from hapic.decorator import InputFilesControllerWrapper
from hapic.decorator import OutputBodyControllerWrapper
from hapic.decorator import OutputHeadersControllerWrapper
from hapic.decorator import OutputFileControllerWrapper
from hapic.description import InputBodyDescription
from hapic.description import ErrorDescription
from hapic.description import InputFormsDescription
from hapic.description import InputHeadersDescription
from hapic.description import InputPathDescription
from hapic.description import InputQueryDescription
from hapic.description import InputFilesDescription
from hapic.description import OutputBodyDescription
from hapic.description import OutputHeadersDescription
from hapic.description import OutputFileDescription
from hapic.doc import DocGenerator
from hapic.processor import ProcessorInterface
from hapic.processor import MarshmallowInputProcessor
from hapic.processor import MarshmallowInputFilesProcessor
from hapic.processor import MarshmallowOutputProcessor


class ErrorResponseSchema(marshmallow.Schema):
    message = marshmallow.fields.String(required=True)
    details = marshmallow.fields.Dict(required=False, missing={})
    code = marshmallow.fields.Raw(missing=None)


_default_global_error_schema = ErrorResponseSchema()


# TODO: Gérer les cas ou c'est une liste la réponse (items, item_nb), see #12
# TODO: Confusion nommage body/json/forms, see #13


class Hapic(object):
    def __init__(self):
        self._buffer = DecorationBuffer()
        self._controllers = []  # type: typing.List[DecoratedController]
        self._context = None  # type: ContextInterface

        # This local function will be pass to different components
        # who will need context but declared (like with decorator)
        # before context declaration
        def context_getter():
            return self._context

        self._context_getter = context_getter

        # TODO: Permettre la surcharge des classes utilisés ci-dessous, see #14

    @property
    def controllers(self) -> typing.List[DecoratedController]:
        return self._controllers

    @property
    def context(self) -> ContextInterface:
        return self._context

    def with_api_doc(self):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            token = uuid.uuid4().hex
            setattr(wrapper, DECORATION_ATTRIBUTE_NAME, token)
            setattr(func, DECORATION_ATTRIBUTE_NAME, token)

            description = self._buffer.get_description()

            reference = ControllerReference(
                wrapper=wrapper,
                wrapped=func,
                token=token,
            )
            decorated_controller = DecoratedController(
                reference=reference,
                description=description,
                name=func.__name__,
            )
            self._buffer.clear()
            self._controllers.append(decorated_controller)
            return wrapper

        return decorator

    def set_context(self, context: ContextInterface) -> None:
        assert not self._context
        self._context = context

    def output_body(
        self,
        schema: typing.Any,
        processor: ProcessorInterface = None,
        context: ContextInterface = None,
        error_http_code: HTTPStatus = HTTPStatus.BAD_REQUEST,
        default_http_code: HTTPStatus = HTTPStatus.OK,
    ) -> typing.Callable[[typing.Callable[..., typing.Any]], typing.Any]:
        processor = processor or MarshmallowOutputProcessor()
        processor.schema = schema
        context = context or self._context_getter
        decoration = OutputBodyControllerWrapper(
            context=context,
            processor=processor,
            error_http_code=error_http_code,
            default_http_code=default_http_code,
        )

        def decorator(func):
            self._buffer.output_body = OutputBodyDescription(decoration)
            return decoration.get_wrapper(func)
        return decorator

    def output_headers(
        self,
        schema: typing.Any,
        processor: ProcessorInterface = None,
        context: ContextInterface = None,
        error_http_code: HTTPStatus = HTTPStatus.BAD_REQUEST,
        default_http_code: HTTPStatus = HTTPStatus.OK,
    ) -> typing.Callable[[typing.Callable[..., typing.Any]], typing.Any]:
        processor = processor or MarshmallowOutputProcessor()
        processor.schema = schema
        context = context or self._context_getter

        decoration = OutputHeadersControllerWrapper(
            context=context,
            processor=processor,
            error_http_code=error_http_code,
            default_http_code=default_http_code,
        )

        def decorator(func):
            self._buffer.output_headers = OutputHeadersDescription(decoration)
            return decoration.get_wrapper(func)
        return decorator

    # TODO BS 20171102: Think about possibilities to validate output ?
    # (with mime type, or validator)
    def output_file(
        self,
        output_types: typing.List[str],
        default_http_code: HTTPStatus = HTTPStatus.OK,
    ) -> typing.Callable[[typing.Callable[..., typing.Any]], typing.Any]:
        decoration = OutputFileControllerWrapper(
            output_types=output_types,
            default_http_code=default_http_code,
        )

        def decorator(func):
            self._buffer.output_file = OutputFileDescription(decoration)
            return decoration.get_wrapper(func)
        return decorator

    def input_headers(
        self,
        schema: typing.Any,
        processor: ProcessorInterface = None,
        context: ContextInterface = None,
        error_http_code: HTTPStatus = HTTPStatus.BAD_REQUEST,
        default_http_code: HTTPStatus = HTTPStatus.OK,
    ) -> typing.Callable[[typing.Callable[..., typing.Any]], typing.Any]:
        processor = processor or MarshmallowInputProcessor()
        processor.schema = schema
        context = context or self._context_getter

        decoration = InputHeadersControllerWrapper(
            context=context,
            processor=processor,
            error_http_code=error_http_code,
            default_http_code=default_http_code,
        )

        def decorator(func):
            self._buffer.input_headers = InputHeadersDescription(decoration)
            return decoration.get_wrapper(func)
        return decorator

    def input_path(
        self,
        schema: typing.Any,
        processor: ProcessorInterface = None,
        context: ContextInterface = None,
        error_http_code: HTTPStatus = HTTPStatus.BAD_REQUEST,
        default_http_code: HTTPStatus = HTTPStatus.OK,
    ) -> typing.Callable[[typing.Callable[..., typing.Any]], typing.Any]:
        processor = processor or MarshmallowInputProcessor()
        processor.schema = schema
        context = context or self._context_getter

        decoration = InputPathControllerWrapper(
            context=context,
            processor=processor,
            error_http_code=error_http_code,
            default_http_code=default_http_code,
        )

        def decorator(func):
            self._buffer.input_path = InputPathDescription(decoration)
            return decoration.get_wrapper(func)
        return decorator

    def input_query(
        self,
        schema: typing.Any,
        processor: ProcessorInterface = None,
        context: ContextInterface = None,
        error_http_code: HTTPStatus = HTTPStatus.BAD_REQUEST,
        default_http_code: HTTPStatus = HTTPStatus.OK,
    ) -> typing.Callable[[typing.Callable[..., typing.Any]], typing.Any]:
        processor = processor or MarshmallowInputProcessor()
        processor.schema = schema
        context = context or self._context_getter

        decoration = InputQueryControllerWrapper(
            context=context,
            processor=processor,
            error_http_code=error_http_code,
            default_http_code=default_http_code,
        )

        def decorator(func):
            self._buffer.input_query = InputQueryDescription(decoration)
            return decoration.get_wrapper(func)
        return decorator

    def input_body(
        self,
        schema: typing.Any,
        processor: ProcessorInterface = None,
        context: ContextInterface = None,
        error_http_code: HTTPStatus = HTTPStatus.BAD_REQUEST,
        default_http_code: HTTPStatus = HTTPStatus.OK,
    ) -> typing.Callable[[typing.Callable[..., typing.Any]], typing.Any]:
        processor = processor or MarshmallowInputProcessor()
        processor.schema = schema
        context = context or self._context_getter

        decoration = InputBodyControllerWrapper(
            context=context,
            processor=processor,
            error_http_code=error_http_code,
            default_http_code=default_http_code,
        )

        def decorator(func):
            self._buffer.input_body = InputBodyDescription(decoration)
            return decoration.get_wrapper(func)
        return decorator

    def input_forms(
        self,
        schema: typing.Any,
        processor: ProcessorInterface=None,
        context: ContextInterface=None,
        error_http_code: HTTPStatus = HTTPStatus.BAD_REQUEST,
        default_http_code: HTTPStatus = HTTPStatus.OK,
    ) -> typing.Callable[[typing.Callable[..., typing.Any]], typing.Any]:
        processor = processor or MarshmallowInputProcessor()
        processor.schema = schema
        context = context or self._context_getter

        decoration = InputBodyControllerWrapper(
            context=context,
            processor=processor,
            error_http_code=error_http_code,
            default_http_code=default_http_code,
        )

        def decorator(func):
            self._buffer.input_forms = InputFormsDescription(decoration)
            return decoration.get_wrapper(func)
        return decorator

    def input_files(
        self,
        schema: typing.Any,
        processor: ProcessorInterface=None,
        context: ContextInterface=None,
        error_http_code: HTTPStatus = HTTPStatus.BAD_REQUEST,
        default_http_code: HTTPStatus = HTTPStatus.OK,
    ) -> typing.Callable[[typing.Callable[..., typing.Any]], typing.Any]:
        processor = processor or MarshmallowInputFilesProcessor()
        processor.schema = schema
        context = context or self._context_getter

        decoration = InputFilesControllerWrapper(
            context=context,
            processor=processor,
            error_http_code=error_http_code,
            default_http_code=default_http_code,
        )

        def decorator(func):
            self._buffer.input_files = InputFilesDescription(decoration)
            return decoration.get_wrapper(func)
        return decorator

    def handle_exception(
        self,
        handled_exception_class: typing.Type[Exception],
        http_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR,
        context: ContextInterface = None,
    ) -> typing.Callable[[typing.Callable[..., typing.Any]], typing.Any]:
        context = context or self._context_getter

        decoration = ExceptionHandlerControllerWrapper(
            handled_exception_class,
            context,
            # TODO BS 20171013: Permit schema overriding, see #15
            schema=_default_global_error_schema,
            http_code=http_code,
        )

        def decorator(func):
            self._buffer.errors.append(ErrorDescription(decoration))
            return decoration.get_wrapper(func)
        return decorator

    def generate_doc(self, app):
        # FIXME: j'ai du tricher avec app, see #11
        # FIXME @Damien bottle specific code ! see #11
        # rendre ca generique
        app = app or self._context.get_app()
        doc_generator = DocGenerator()
        return doc_generator.get_doc(self._controllers, app)
