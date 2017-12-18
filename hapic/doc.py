# -*- coding: utf-8 -*-
import typing

from apispec import APISpec
from apispec import Path
from apispec.ext.marshmallow.swagger import schema2jsonschema

from hapic.context import ContextInterface
from hapic.context import RouteRepresentation
from hapic.decorator import DecoratedController
from hapic.description import ControllerDescription


def bottle_generate_operations(
    spec,
    route: RouteRepresentation,
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
                'description': int(description.output_body.wrapper.default_http_code),  # nopep8
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
            'description': int(description.output_file.wrapper.default_http_code),  # nopep8
        }

    if description.errors:
        for error in description.errors:
            schema_class = type(error.wrapper.schema)
            method_operations.setdefault('responses', {})\
                [int(error.wrapper.http_code)] = {
                    'description': int(error.wrapper.http_code),
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
        route.method.lower(): method_operations,
    }

    return operations


class DocGenerator(object):
    def get_doc(
        self,
        controllers: typing.List[DecoratedController],
        context: ContextInterface,
        title: str='',
        description: str='',
    ) -> dict:
        spec = APISpec(
            title=title,
            info=dict(description=description),
            version='1.0.0',
            plugins=(
                'apispec.ext.marshmallow',
            ),
            schema_name_resolver=generate_schema_name,
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
            route = context.find_route(controller)
            swagger_path = context.get_swagger_path(route.rule)

            operations = bottle_generate_operations(
                spec,
                route,
                controller.description,
            )

            # TODO BS 20171114: TMP code waiting refact of doc
            doc_string = controller.reference.get_doc_string()
            if doc_string:
                for method in operations.keys():
                    operations[method]['description'] = doc_string

            path = Path(path=swagger_path, operations=operations)

            if swagger_path in paths:
                paths[swagger_path].update(path)
            else:
                paths[swagger_path] = path

            spec.add_path(path)

        return spec.to_dict()


# TODO BS 20171109: Must take care of already existing definition names
def generate_schema_name(schema):
    return schema.__name__
