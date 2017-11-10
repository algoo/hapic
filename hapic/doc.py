# -*- coding: utf-8 -*-
import re
import typing

import bottle
from apispec import APISpec
from apispec import Path
from apispec.ext.marshmallow.swagger import schema2jsonschema

from hapic.decorator import DecoratedController
from hapic.decorator import DECORATION_ATTRIBUTE_NAME
from hapic.description import ControllerDescription
from hapic.exception import NoRoutesException
from hapic.exception import RouteNotFound

# Bottle regular expression to locate url parameters
BOTTLE_RE_PATH_URL = re.compile(r'<(?:[^:<>]+:)?([^<>]+)>')


def find_bottle_route(
    decorated_controller: DecoratedController,
    app: bottle.Bottle,
):
    if not app.routes:
        raise NoRoutesException('There is no routes in your bottle app')

    reference = decorated_controller.reference
    for route in app.routes:
        route_token = getattr(
            route.callback,
            DECORATION_ATTRIBUTE_NAME,
            None,
        )

        match_with_wrapper = route.callback == reference.wrapper
        match_with_wrapped = route.callback == reference.wrapped
        match_with_token = route_token == reference.token

        if match_with_wrapper or match_with_wrapped or match_with_token:
            return route
    # TODO BS 20171010: Raise exception or print error ? see #10
    raise RouteNotFound(
        'Decorated route "{}" was not found in bottle routes'.format(
            decorated_controller.name,
        )
    )


def bottle_generate_operations(
    spec,
    bottle_route: bottle.Route,
    description: ControllerDescription,
):
    method_operations = dict()

    # schema based
    if description.input_body:
        schema_class = type(description.input_body.wrapper.processor.schema)
        method_operations.setdefault('parameters', []).append({
            'in': 'body',
            'name': 'body',
            'schema': {
                '$ref': '#/definitions/{}'.format(schema_class.__name__)
            }
        })

    if description.output_body:
        schema_class = type(description.output_body.wrapper.processor.schema)
        method_operations.setdefault('responses', {})\
            [int(description.output_body.wrapper.default_http_code)] = {
                'description': str(description.output_body.wrapper.default_http_code),  # nopep8
                'schema': {
                    '$ref': '#/definitions/{}'.format(schema_class.__name__)
                }
            }

    if description.output_file:
        method_operations.setdefault('produces', []).extend(
            description.output_file.wrapper.output_types
        )
        method_operations.setdefault('responses', {})\
            [int(description.output_file.wrapper.default_http_code)] = {
            'description': str(description.output_file.wrapper.default_http_code),  # nopep8
        }

    if description.errors:
        for error in description.errors:
            schema_class = type(error.wrapper.schema)
            method_operations.setdefault('responses', {})\
                [int(error.wrapper.http_code)] = {
                    'description': str(error.wrapper.http_code),
                    'schema': {
                        '$ref': '#/definitions/{}'.format(schema_class.__name__)  # nopep8
                    }
                }

    # jsonschema based
    if description.input_path:
        schema_class = type(description.input_path.wrapper.processor.schema)
        # TODO: look schema2parameters ?
        jsonschema = schema2jsonschema(schema_class, spec=spec)
        for name, schema in jsonschema.get('properties', {}).items():
            method_operations.setdefault('parameters', []).append({
                'in': 'path',
                'name': name,
                'required': name in jsonschema.get('required', []),
                'type': schema['type']
            })

    if description.input_query:
        schema_class = type(description.input_query.wrapper.processor.schema)
        jsonschema = schema2jsonschema(schema_class, spec=spec)
        for name, schema in jsonschema.get('properties', {}).items():
            method_operations.setdefault('parameters', []).append({
                'in': 'query',
                'name': name,
                'required': name in jsonschema.get('required', []),
                'type': schema['type']
            })

    if description.input_files:
        method_operations.setdefault('consumes', []).append('multipart/form-data')
        for field_name, field in description.input_files.wrapper.processor.schema.fields.items():
            method_operations.setdefault('parameters', []).append({
                'in': 'formData',
                'name': field_name,
                'required': field.required,
                'type': 'file',
            })

    operations = {
        bottle_route.method.lower(): method_operations,
    }

    return operations


class DocGenerator(object):
    def get_doc(
        self,
        controllers: typing.List[DecoratedController],
        app,
    ) -> dict:
        # TODO: Découper, see #11
        # TODO: bottle specific code !, see #11
        if not app:
            app = bottle.default_app()
        else:
            bottle.default_app.push(app)
        flatten = lambda l: [item for sublist in l for item in sublist]

        spec = APISpec(
            title='Swagger Petstore',
            version='1.0.0',
            plugins=[
                'apispec.ext.bottle',
                'apispec.ext.marshmallow',
            ],
            schema_name_resolver_callable=generate_schema_name,
        )

        schemas = []
        # parse schemas
        for controller in controllers:
            description = controller.description

            if description.input_body:
                schemas.append(type(
                    description.input_body.wrapper.processor.schema
                ))

            if description.input_forms:
                schemas.append(type(
                    description.input_forms.wrapper.processor.schema
                ))

            if description.output_body:
                schemas.append(type(
                    description.output_body.wrapper.processor.schema
                ))

            if description.errors:
                for error in description.errors:
                    schemas.append(type(error.wrapper.schema))

        for schema in set(schemas):
            spec.definition(schema.__name__, schema=schema)

        # add views
        # with app.test_request_context():
        paths = {}
        for controller in controllers:
            bottle_route = find_bottle_route(controller, app)
            swagger_path = BOTTLE_RE_PATH_URL.sub(r'{\1}', bottle_route.rule)

            operations = bottle_generate_operations(
                spec,
                bottle_route,
                controller.description,
            )

            path = Path(path=swagger_path, operations=operations)

            if swagger_path in paths:
                paths[swagger_path].update(path)
            else:
                paths[swagger_path] = path

            spec.add_path(path)

        return spec.to_dict()

        # route_by_callbacks = []
        # routes = flatten(app.router.dyna_routes.values())
        # for path, path_regex, route, func_ in routes:
        #     route_by_callbacks.append(route.callback)
        #
        # for description in self._controllers:
        #     for path, path_regex, route, func_ in routes:
        #         if route.callback == description.reference:
        #             # TODO: use description to feed apispec
        #             print(route.method, path, description)
        #             continue


# TODO BS 20171109: Must take care of already existing definition names
def generate_schema_name(schema):
    return schema.__name__
