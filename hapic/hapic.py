# -*- coding: utf-8 -*-
import os
import typing
import uuid
import functools
try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus

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
from hapic.error import ErrorBuilderInterface


# TODO: Gérer les cas ou c'est une liste la réponse (items, item_nb), see #12
# TODO: Confusion nommage body/json/forms, see #13


class Hapic(object):
    def __init__(self):
        self._buffer = DecorationBuffer()
        self._controllers = []  # type: typing.List[DecoratedController]
        self._context = None  # type: ContextInterface
        self._error_builder = None  # type: ErrorBuilderInterface
        self.doc_generator = DocGenerator()

        # This local function will be pass to different components
        # who will need context but declared (like with decorator)
        # before context declaration
        def context_getter():
            return self._context

        # This local function will be pass to different components
        # who will need error_builder but declared (like with decorator)
        # before error_builder declaration
        def error_builder_getter():
            return self._context.get_default_error_builder()

        self._context_getter = context_getter
        self._error_builder_getter = error_builder_getter

        # TODO: Permettre la surcharge des classes utilisés ci-dessous, see #14

    @property
    def controllers(self) -> typing.List[DecoratedController]:
        return self._controllers

    @property
    def context(self) -> ContextInterface:
        return self._context

    def set_context(self, context: ContextInterface) -> None:
        assert not self._context
        self._context = context

    def reset_context(self) -> None:
        self._context = None

    def with_api_doc(self, tags: typing.List['str']=None):
        """
        Permit to generate doc about a controller. Use as a decorator:

        ```
        @hapic.with_api_doc()
        def my_controller(self):
            # ...
        ```

        What it do: Register this controller with all previous given
        information like `@hapic.input_path(...)` etc.

        :param tags: list of string tags (OpenApi)
        :return: The decorator
        """
        # FIXME BS 20171228: Documenter sur ce que ça fait vraiment (tester:
        # on peut l'enlever si on veut pas generer la doc ?)
        tags = tags or []  # FDV

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            token = uuid.uuid4().hex
            setattr(wrapper, DECORATION_ATTRIBUTE_NAME, token)
            setattr(func, DECORATION_ATTRIBUTE_NAME, token)

            description = self._buffer.get_description()
            description.tags = tags

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

    def output_body(
        self,
        schema: typing.Any,
        processor: ProcessorInterface = None,
        context: ContextInterface = None,
        error_http_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR,
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
        as_list: typing.List[str]=None,
    ) -> typing.Callable[[typing.Callable[..., typing.Any]], typing.Any]:
        processor = processor or MarshmallowInputProcessor()
        processor.schema = schema
        context = context or self._context_getter

        decoration = InputQueryControllerWrapper(
            context=context,
            processor=processor,
            error_http_code=error_http_code,
            default_http_code=default_http_code,
            as_list=as_list,
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
        handled_exception_class: typing.Type[Exception]=Exception,
        http_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR,
        error_builder: ErrorBuilderInterface=None,
        context: ContextInterface = None,
    ) -> typing.Callable[[typing.Callable[..., typing.Any]], typing.Any]:
        context = context or self._context_getter
        error_builder = error_builder or self._error_builder_getter

        decoration = ExceptionHandlerControllerWrapper(
            handled_exception_class,
            context,
            error_builder=error_builder,
            http_code=http_code,
        )

        def decorator(func):
            self._buffer.errors.append(ErrorDescription(decoration))
            return decoration.get_wrapper(func)
        return decorator

    def generate_doc(self, title: str='', description: str='') -> dict:
        """
        See hapic.doc.DocGenerator#get_doc docstring
        :param title: Title of generated doc
        :param description: Description of generated doc
        :return: dict containing apispec doc
        """
        return self.doc_generator.get_doc(
            self._controllers,
            self.context,
            title=title,
            description=description,
        )

    def save_doc_in_file(
        self,
        file_path: str,
        title: str='',
        description: str='',
    ) -> None:
        """
        See hapic.doc.DocGenerator#get_doc docstring
        :param file_path: The file path to write doc in YAML format
        :param title: Title of generated doc
        :param description: Description of generated doc
        """
        self.doc_generator.save_in_file(
            file_path,
            controllers=self._controllers,
            context=self.context,
            title=title,
            description=description,
        )

    def add_documentation_view(
        self,
        route: str,
        title: str='',
        description: str='',
    ) -> None:
        # Ensure "/" at end of route, else web browser will not consider it as
        # a path
        if not route.endswith('/'):
            route = '{}/'.format(route)

        swaggerui_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'static',
            'swaggerui',
        )

        # Documentation file view
        doc_yaml = self.doc_generator.get_doc_yaml(
            controllers=self._controllers,
            context=self.context,
            title=title,
            description=description,
        )

        def spec_yaml_view(*args, **kwargs):
            """
            Method to return swagger generated yaml spec file.

            This method will be call as a framework view, like those,
            it need to handle the default arguments of a framework view.
            As frameworks have different arguments patterns, we should
            allow any arguments patterns (args, kwargs).
            """
            return self.context.get_response(
                doc_yaml,
                mimetype='text/x-yaml',
                http_code=HTTPStatus.OK,
            )

        # Prepare views html content
        doc_index_path = os.path.join(swaggerui_path, 'index.html')
        with open(doc_index_path, 'r') as doc_page:
            doc_page_content = doc_page.read()
        doc_page_content = doc_page_content.replace(
            '{{ spec_uri }}',
            'spec.yml',
        )

        # Declare the swaggerui view
        def api_doc_view(*args, **kwargs):
            """
            Method to return html index view of swagger ui.

            This method will be call as a framework view, like those,
            it need to handle the default arguments of a framework view.
            As frameworks have different arguments patterns, we should
            allow any arguments patterns (args, kwargs).
            """
            return self.context.get_response(
                doc_page_content,
                http_code=HTTPStatus.OK,
                mimetype='text/html',
            )

        # Add a view to generate the html index page of swagger-ui
        self.context.add_view(
            route=route,
            http_method='GET',
            view_func=api_doc_view,
        )

        # Add a doc yaml view
        self.context.add_view(
            route=os.path.join(route, 'spec.yml'),
            http_method='GET',
            view_func=spec_yaml_view,
        )

        # Add swagger directory as served static dir
        self.context.serve_directory(
            route,
            swaggerui_path,
        )
