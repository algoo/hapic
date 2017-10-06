# -*- coding: utf-8 -*-
import typing
from http import HTTPStatus
import functools

import marshmallow

from hapic.buffer import DecorationBuffer
from hapic.context import ContextInterface, BottleContext
from hapic.decorator import DecoratedController
from hapic.decorator import ExceptionHandlerControllerWrapper
from hapic.decorator import InputBodyControllerWrapper
from hapic.decorator import InputHeadersControllerWrapper
from hapic.decorator import InputPathControllerWrapper
from hapic.decorator import InputQueryControllerWrapper
from hapic.decorator import OutputBodyControllerWrapper
from hapic.decorator import OutputHeadersControllerWrapper
from hapic.description import InputBodyDescription, ErrorDescription
from hapic.description import InputFormsDescription
from hapic.description import InputHeadersDescription
from hapic.description import InputPathDescription
from hapic.description import InputQueryDescription
from hapic.description import OutputBodyDescription
from hapic.description import OutputHeadersDescription
from hapic.doc import DocGenerator
from hapic.processor import ProcessorInterface
from hapic.processor import MarshmallowInputProcessor

# TODO: Gérer les erreurs avec schema
# TODO: Gérer les erreurs avec schema: pouvoir le spécialiser
# TODO: Gérer les cas ou c'est une liste la réponse (items, item_nb)
# TODO: Confusion nommage body/json/forms

# _waiting = {}
# _endpoints = {}
# FIXME: Voir
class ErrorResponseSchema(marshmallow.Schema):
    error_message = marshmallow.fields.String(required=True)


    error_details = marshmallow.fields.Dict(required=True)
# FIXME: C'est un gros gros fake !
_default_global_error_schema = ErrorResponseSchema()


class Hapic(object):
    def __init__(self):
        self._buffer = DecorationBuffer()
        self._controllers = []  # type: typing.List[DecoratedController]
        self._context = None
        # TODO: Permettre la surcharge des classes utilisés ci-dessous

    def with_api_doc(self):
        def decorator(func):

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            description = self._buffer.get_description()
            decorated_controller = DecoratedController(
                reference=wrapper,
                description=description,
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
        processor = processor or MarshmallowInputProcessor()
        processor.schema = schema
        context = context or self._context

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
        processor = processor or MarshmallowInputProcessor()
        processor.schema = schema
        context = context or self._context

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
        context = context or self._context

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
        context = context or self._context

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
        context = context or self._context

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
        context = context or self._context

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
        context = context or self._context

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

    def handle_exception(
        self,
        handled_exception_class: typing.Type[Exception],
        http_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR,
        context: ContextInterface = None,
    ) -> typing.Callable[[typing.Callable[..., typing.Any]], typing.Any]:
        context = context or self._context

        decoration = ExceptionHandlerControllerWrapper(
            handled_exception_class,
            context,
            http_code,
        )

        def decorator(func):
            self._buffer.errors.append(ErrorDescription(decoration))
            return decoration.get_wrapper(func)
        return decorator

    def generate_doc(self):
        # FIXME @Damien bottle specific code !
        # rendre ca generique
        app = self._context.get_app()
        doc_generator = DocGenerator()
        return doc_generator.get_doc(self._controllers, app)
