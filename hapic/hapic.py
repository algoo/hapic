# -*- coding: utf-8 -*-
import json
import typing

import functools

import bottle

# TODO: Gérer les erreurs de schema
# TODO: Gérer les cas ou c'est une liste la réponse (items, item_nb)


# CHANGE
flatten = lambda l: [item for sublist in l for item in sublist]


_waiting = {}
_endpoints = {}
_default_global_context = None


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


class ContextInterface(object):
    def get_request_parameters(self, *args, **kwargs) -> RequestParameters:
        raise NotImplementedError()

    def get_response(
        self,
        response: dict,
        http_code: int,
    ):
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


class OutputProcessorInterface(object):
    def __init__(self):
        self.schema = None

    def process(self, value):
        raise NotImplementedError


class InputProcessorInterface(object):
    def __init__(self):
        self.schema = None

    def process(self, request_context: RequestParameters):
        raise NotImplementedError


class MarshmallowOutputProcessor(OutputProcessorInterface):
    def process(self, data: typing.Any):
        return self.schema.dump(data).data


class MarshmallowInputProcessor(OutputProcessorInterface):
    def process(self, data: dict):
        return self.schema.load(data).data


# class MarshmallowPathInputProcessor(OutputProcessorInterface):
#     def process(self, request_context: RequestParameters):
#         return self.schema.load(request_context.path_parameters).data
#
#
# class MarshmallowQueryInputProcessor(OutputProcessorInterface):
#     def process(self, request_context: RequestParameters):
#         return self.schema.load(request_context.query_parameters).data
#
#
# class MarshmallowJsonInputProcessor(OutputProcessorInterface):
#     def process(self, request_context: RequestParameters):
#         return self.schema.load(request_context.json_parameters).data


# class MarshmallowFormInputProcessor(OutputProcessorInterface):
#     def process(self, request_context: RequestParameters):
#         return self.schema.load(xxx).data
#
#
# class MarshmallowHeaderInputProcessor(OutputProcessorInterface):
#     def process(self, request_context: RequestParameters):
#         return self.schema.load(xxx).data


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
            hapic_data.body = processor.process(request_parameters.body_parameters)

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
