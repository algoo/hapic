# -*- coding: utf-8 -*-
import json
import typing
from http import HTTPStatus

import functools

import bottle

# TODO: Gérer les erreurs de schema
# TODO: Gérer les cas ou c'est une liste la réponse (items, item_nb)


# CHANGE
from hapic.exception import InputValidationException, \
    OutputValidationException, InputWorkflowException, ProcessException

flatten = lambda l: [item for sublist in l for item in sublist]


_waiting = {}
_endpoints = {}
_default_global_context = None
_default_global_error_schema = None


def error_schema(schema):
    global _default_global_error_schema
    _default_global_error_schema = schema

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def set_fake_default_context(context):
    global _default_global_context
    _default_global_context = context


def _register(func):
    assert func not in _endpoints
    global _waiting

    _endpoints[func] = _waiting
    _waiting = {}


def with_api_doc():
    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        _register(wrapper)
        return wrapper

    return decorator


def with_api_doc_bis():
    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        _register(func)
        return wrapper

    return decorator


def generate_doc(app=None):
    # TODO @Damien bottle specific code !
    app = app or bottle.default_app()

    route_by_callbacks = []
    routes = flatten(app.router.dyna_routes.values())
    for path, path_regex, route, func_ in routes:
        route_by_callbacks.append(route.callback)

    for func, descriptions in _endpoints.items():
        routes = flatten(app.router.dyna_routes.values())
        for path, path_regex, route, func_ in routes:
            if route.callback == func:
                print(route.method, path, descriptions)
                continue


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


class ContextInterface(object):
    def get_request_parameters(self, *args, **kwargs) -> RequestParameters:
        raise NotImplementedError()

    def get_response(
        self,
        response: dict,
        http_code: int,
    ) -> typing.Any:
        raise NotImplementedError()

    def get_validation_error_response(
        self,
        error: ProcessValidationError,
        http_code: HTTPStatus=HTTPStatus.BAD_REQUEST,
    ) -> typing.Any:
        raise NotImplementedError()


class BottleContext(ContextInterface):
    def get_request_parameters(self, *args, **kwargs) -> RequestParameters:
        return RequestParameters(
            path_parameters=bottle.request.url_args,
            query_parameters=bottle.request.params,
            body_parameters=bottle.request.json,
            form_parameters=bottle.request.forms,
            header_parameters=bottle.request.headers,
        )

    def get_response(
        self,
        response: dict,
        http_code: int,
    ) -> bottle.HTTPResponse:
        return bottle.HTTPResponse(
            body=json.dumps(response),
            headers=[
                ('Content-Type', 'application/json'),
            ],
            status=http_code,
        )

    def get_validation_error_response(
        self,
        error: ProcessValidationError,
        http_code: HTTPStatus=HTTPStatus.BAD_REQUEST,
    ) -> typing.Any:
        unmarshall = _default_global_error_schema.dump(error)
        if unmarshall.errors:
            raise OutputValidationException(
                'Validation error during dump of error response: {}'.format(
                    str(unmarshall.errors)
                )
            )

        return bottle.HTTPResponse(
            body=json.dumps(unmarshall.data),
            headers=[
                ('Content-Type', 'application/json'),
            ],
            status=int(http_code),
        )


class OutputProcessorInterface(object):
    def __init__(self):
        self.schema = None

    def process(self, value):
        raise NotImplementedError

    def get_validation_error(
        self,
        request_context: RequestParameters,
    ) -> ProcessValidationError:
        raise NotImplementedError


class InputProcessorInterface(object):
    def __init__(self):
        self.schema = None

    def process(
        self,
        request_context: RequestParameters,
    ) -> typing.Any:
        raise NotImplementedError

    def get_validation_error(
        self,
        request_context: RequestParameters,
    ) -> ProcessValidationError:
        raise NotImplementedError


class MarshmallowOutputProcessor(OutputProcessorInterface):
    def process(self, data: typing.Any):
        unmarshall = self.schema.dump(data)
        if unmarshall.errors:
            raise InputValidationException(
                'Error when validate input: {}'.format(
                    str(unmarshall.errors),
                )
            )

        return unmarshall.data

    def get_validation_error(self, data: dict) -> ProcessValidationError:
        marshmallow_errors = self.schema.dump(data).errors
        return ProcessValidationError(
            error_message='Validation error of output data',
            error_details=marshmallow_errors,
        )


class MarshmallowInputProcessor(OutputProcessorInterface):
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


class HapicData(object):
    def __init__(self):
        self.body = {}
        self.path = {}
        self.query = {}
        self.headers = {}


# TODO: Il faut un output_body et un output_header
def output(
    schema,
    processor: OutputProcessorInterface=None,
    context: ContextInterface=None,
    default_http_code=200,
    default_error_code=500,
):
    processor = processor or MarshmallowOutputProcessor()
    processor.schema = schema
    context = context or _default_global_context

    def decorator(func):
        # @functools.wraps(func)
        def wrapper(*args, **kwargs):
            raw_response = func(*args, **kwargs)
            processed_response = processor.process(raw_response)
            prepared_response = context.get_response(
                processed_response,
                default_http_code,
            )
            return prepared_response

        _waiting['output'] = schema

        return wrapper
    return decorator

# TODO: raccourcis 'input' tout court ?
def input_body(
    schema,
    processor: InputProcessorInterface=None,
    context: ContextInterface=None,
    error_http_code: HTTPStatus=HTTPStatus.BAD_REQUEST,
):
    processor = processor or MarshmallowInputProcessor()
    processor.schema = schema
    context = context or _default_global_context

    def decorator(func):

        # @functools.wraps(func)
        def wrapper(*args, **kwargs):
            updated_kwargs = {'hapic_data': HapicData()}
            updated_kwargs.update(kwargs)
            hapic_data = updated_kwargs['hapic_data']

            request_parameters = context.get_request_parameters(
                *args,
                **updated_kwargs
            )

            try:
                hapic_data.body = processor.process(
                    request_parameters.body_parameters,
                )
            except ProcessException:
                error = processor.get_validation_error(
                    request_parameters.body_parameters,
                )
                error_response = context.get_validation_error_response(
                    error,
                    http_code=error_http_code,
                )
                return error_response

            return func(*args, **updated_kwargs)

        _waiting.setdefault('input', []).append(schema)

        return wrapper
    return decorator


def input_path(
    schema,
    processor: InputProcessorInterface=None,
    context: ContextInterface=None,
    error_http_code=400,
):
    processor = processor or MarshmallowInputProcessor()
    processor.schema = schema
    context = context or _default_global_context

    def decorator(func):

        # @functools.wraps(func)
        def wrapper(*args, **kwargs):
            updated_kwargs = {'hapic_data': HapicData()}
            updated_kwargs.update(kwargs)
            hapic_data = updated_kwargs['hapic_data']

            request_parameters = context.get_request_parameters(*args, **updated_kwargs)
            hapic_data.path = processor.process(request_parameters.path_parameters)

            return func(*args, **updated_kwargs)

        _waiting.setdefault('input', []).append(schema)

        return wrapper
    return decorator


def input_query(
    schema,
    processor: InputProcessorInterface=None,
    context: ContextInterface=None,
    error_http_code=400,
):
    processor = processor or MarshmallowInputProcessor()
    processor.schema = schema
    context = context or _default_global_context

    def decorator(func):

        # @functools.wraps(func)
        def wrapper(*args, **kwargs):
            updated_kwargs = {'hapic_data': HapicData()}
            updated_kwargs.update(kwargs)
            hapic_data = updated_kwargs['hapic_data']

            request_parameters = context.get_request_parameters(*args, **updated_kwargs)
            hapic_data.query = processor.process(request_parameters.query_parameters)

            return func(*args, **updated_kwargs)

        _waiting.setdefault('input', []).append(schema)

        return wrapper
    return decorator


def input_headers(
    schema,
    processor: InputProcessorInterface,
    context: ContextInterface=None,
    error_http_code=400,
):
    processor = processor or MarshmallowInputProcessor()
    processor.schema = schema
    context = context or _default_global_context

    def decorator(func):

        # @functools.wraps(func)
        def wrapper(*args, **kwargs):
            updated_kwargs = {'hapic_data': HapicData()}
            updated_kwargs.update(kwargs)
            hapic_data = updated_kwargs['hapic_data']

            request_parameters = context.get_request_parameters(*args, **updated_kwargs)
            hapic_data.headers = processor.process(request_parameters.header_parameters)

            return func(*args, **updated_kwargs)

        _waiting.setdefault('input', []).append(schema)

        return wrapper
    return decorator
