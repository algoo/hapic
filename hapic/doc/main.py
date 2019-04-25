# coding: utf-8
import json
import typing

from apispec import APISpec
from apispec import BasePlugin
from apispec.exceptions import DuplicateComponentNameError
import yaml

from hapic.context import ContextInterface
from hapic.context import RouteRepresentation
from hapic.decorator import DecoratedController
from hapic.description import ControllerDescription
from hapic.doc.schema import SchemaUsage

if typing.TYPE_CHECKING:
    from hapic.hapic import Hapic


FIELDS_PARAMS_GENERIC_ACCEPTED = ["type", "format", "required", "description", "enum"]
FIELDS_TYPE_ARRAY = ["array"]
FIELDS_PARAMS_ARRAY_ACCEPTED = [
    "items",
    "collectionFormat",
    "pattern",
    "maxitems",
    "minitems",
    "uniqueitems",
]
FIELDS_TYPE_STRING = ["string"]
FIELDS_PARAMS_STRING_ACCEPTED = ["maxLength", "minLength", "pattern"]
FIELDS_TYPE_NUMERIC = ["number", "integer"]
FIELDS_PARAMS_NUMERIC_ACCEPTED = [
    "maximum",
    "exclusiveMaximum",
    "minimum",
    "exclusiveMinimum",
    "multipleOf",
]


def field_accepted_param(type: str, param_name: str) -> bool:
    return (
        param_name in FIELDS_PARAMS_GENERIC_ACCEPTED
        or (type in FIELDS_TYPE_STRING and param_name in FIELDS_PARAMS_STRING_ACCEPTED)
        or (type in FIELDS_TYPE_ARRAY and param_name in FIELDS_PARAMS_ARRAY_ACCEPTED)
        or (type in FIELDS_TYPE_NUMERIC and param_name in FIELDS_PARAMS_NUMERIC_ACCEPTED)
    )


def generate_fields_description(
    schema, in_: str, name: str, required: bool, type: str = None
) -> dict:
    """
    Generate field OpenApiDescription for
    both query and path params
    :param schema: field schema
    :param in_: in field
    :param name: field name
    :param required: required field
    :param type: type field
    :return: File description for OpenApi
    """
    description = {}
    # INFO - G.M - 01-06-2018 - get field
    # type to know which params are accepted
    if not type and "type" in schema:
        type = schema["type"]
    assert type

    for param_name, value in schema.items():
        if field_accepted_param(type, param_name):
            description[param_name] = value
    description["type"] = type
    description["in"] = in_
    description["name"] = name
    description["required"] = required

    # INFO - G.M - 01-06-2018 - example is not allowed in query/path params,
    # in OpenApi2, remove it and set it as string in field description.
    if "example" in schema:
        if "description" not in description:
            description["description"] = ""
        description["description"] = "{description}\n\n*example value: {example}*".format(
            description=description["description"], example=schema["example"]
        )
    return description


def generate_operations(
    main_plugin: BasePlugin, route: RouteRepresentation, description: ControllerDescription
):
    method_operations = dict()
    if description.input_body:
        schema_ref = description.input_body.wrapper.processor.generate_schema_ref(main_plugin)
        method_operations.setdefault("parameters", []).append(
            {"in": "body", "name": "body", "schema": schema_ref}
        )

    if description.output_body:
        schema_ref = description.output_body.wrapper.processor.generate_schema_ref(main_plugin)
        method_operations.setdefault("responses", {})[
            int(description.output_body.wrapper.default_http_code)
        ] = {
            "description": str(int(description.output_body.wrapper.default_http_code)),
            "schema": schema_ref,
        }

    if description.output_stream:
        schema_ref = description.output_stream.wrapper.processor.generate_schema_ref(main_plugin)
        method_operations.setdefault("responses", {})[
            int(description.output_stream.wrapper.default_http_code)
        ] = {
            "description": str(int(description.output_stream.wrapper.default_http_code)),
            "schema": {"type": "array", "items": schema_ref},
        }

    if description.output_file:
        method_operations.setdefault("produces", []).extend(
            description.output_file.wrapper.output_types
        )
        method_operations.setdefault("responses", {})[
            int(description.output_file.wrapper.default_http_code)
        ] = {"description": str(int(description.output_file.wrapper.default_http_code))}

    if description.errors:
        http_status_errors = {}
        for error in description.errors:
            http_status_errors.setdefault(error.wrapper.error_http_code, []).append(error)

        for http_status in http_status_errors:
            # FIXME - G.M - 2018-11-30 - We use schema class from first error
            # for each status as openapi 2.0 doesn't support different schema
            # result. This may cause incoherent result.
            default_error = http_status_errors[http_status][0]
            schema_class = default_error.wrapper.error_builder.get_schema()
            errors_description = set()
            for error in http_status_errors[http_status]:
                errors_description.add(error.wrapper.description)

            method_operations.setdefault("responses", {})[int(http_status)] = {
                "description": "\n\n".join(errors_description),
                "schema": {
                    "$ref": "#/definitions/{}".format(
                        main_plugin.schema_name_resolver(schema_class)
                    )
                },
            }

    # jsonschema based
    if description.input_path:
        schema_usage = description.input_path.wrapper.processor.schema_class_resolver(main_plugin)
        jsonschema = main_plugin.schema_helper(
            main_plugin.schema_name_resolver(
                schema_usage.schema, **schema_usage.plugin_name_resolver_kwargs
            ),
            # INFO - G.M - 2019-03-19 - _ is required but
            # not found what it means in apispec code.
            _=None,
            schema=schema_usage.schema,
            **schema_usage.plugin_helper_kwargs,
        )

        for name, schema in jsonschema.get("properties", {}).items():
            method_operations.setdefault("parameters", []).append(
                generate_fields_description(
                    schema=schema,
                    in_="path",
                    name=name,
                    required=name in jsonschema.get("required", []),
                )
            )

    if description.input_query:
        schema_usage = description.input_query.wrapper.processor.schema_class_resolver(main_plugin)
        jsonschema = main_plugin.schema_helper(
            main_plugin.schema_name_resolver(
                schema_usage.schema, **schema_usage.plugin_name_resolver_kwargs
            ),
            # INFO - G.M - 2019-03-19 - _ is required but
            # not found what it means in apispec code.
            _=None,
            schema=schema_usage.schema,
            **schema_usage.plugin_helper_kwargs,
        )

        for name, schema in jsonschema.get("properties", {}).items():
            method_operations.setdefault("parameters", []).append(
                generate_fields_description(
                    schema=schema,
                    in_="query",
                    name=name,
                    required=name in jsonschema.get("required", []),
                )
            )

    if description.input_files or description.input_forms:
        method_operations.setdefault("consumes", []).append("multipart/form-data")

    if description.input_files:
        jsonschema = main_plugin.openapi.schema2jsonschema(
            description.input_files.wrapper.processor.schema
        )
        for name, schema in jsonschema.get("properties", {}).items():
            method_operations.setdefault("parameters", []).append(
                generate_fields_description(
                    schema=schema,
                    in_="formData",
                    name=name,
                    required=name in jsonschema.get("required", []),
                    type="file",
                )
            )
    if description.input_forms:
        jsonschema = main_plugin.openapi.schema2jsonschema(
            description.input_forms.wrapper.processor.schema
        )
        for name, schema in jsonschema.get("properties", {}).items():
            method_operations.setdefault("parameters", []).append(
                generate_fields_description(
                    schema=schema,
                    in_="formData",
                    name=name,
                    required=name in jsonschema.get("required", []),
                )
            )

    if description.tags:
        method_operations["tags"] = description.tags

    operations = {route.method.lower(): method_operations}

    return operations


class DocGenerator(object):
    def get_doc(
        self,
        hapic: "Hapic",
        controllers: typing.List[DecoratedController],
        context: ContextInterface,
        title: str = "",
        description: str = "",
        version: str = "1.0.0",
    ) -> dict:
        """
        Generate an OpenApi 2.0 documentation. Th given context will be used
        to found controllers matching with given DecoratedController.
        :param controllers: List of DecoratedController to match with context
        controllers
        :param context: a context instance
        :param title: The generated doc title
        :param description: The generated doc description
        :return: a apispec documentation dict
        """
        main_plugin = hapic.processor_class.create_apispec_plugin()

        plugins = (main_plugin,)
        spec = APISpec(
            title=title,
            info=dict(description=description),
            version=version,
            plugins=plugins,
            openapi_version="2.0",
        )

        schema_usages = []  # type: typing.List[SchemaUsage]
        # Parse used schema and pre-index them into apispec plugin
        for controller in controllers:
            description = controller.description

            for description_item in [
                description.input_body,
                description.input_path,
                description.input_query,
                description.input_forms,
                description.output_body,
            ]:
                if description_item:
                    schema_usage = description_item.wrapper.processor.schema_class_resolver(
                        main_plugin
                    )
                    schema_usages.append(schema_usage)

            if description.errors:
                for error in description.errors:
                    error_schema = error.wrapper.error_builder.get_schema()
                    schema_usages.append(SchemaUsage(error_schema))

        for schema_usage in set(schema_usages):
            try:
                spec.components.schema(
                    main_plugin.schema_name_resolver(
                        schema_usage.schema, **schema_usage.plugin_name_resolver_kwargs
                    ),
                    schema=schema_usage.schema,
                    **schema_usage.plugin_helper_kwargs,
                )
            except DuplicateComponentNameError:
                pass  # Already registered schema

        # add views
        for controller in controllers:
            if controller.description.disable_doc:
                continue

            route = context.find_route(controller)
            swagger_path = context.get_swagger_path(route.rule)

            operations = generate_operations(main_plugin, route, controller.description)

            doc_string = controller.reference.get_doc_string()
            if doc_string:
                for method in operations.keys():
                    operations[method]["description"] = doc_string

            spec.path(swagger_path, operations=operations)

        return spec.to_dict()

    def get_doc_yaml(
        self,
        hapic: "Hapic",
        controllers: typing.List[DecoratedController],
        context: ContextInterface,
        title: str = "",
        description: str = "",
        version: str = "1.0.0",
    ) -> str:
        dict_doc = self.get_doc(
            hapic=hapic,
            controllers=controllers,
            context=context,
            title=title,
            description=description,
            version=version,
        )
        json_doc = json.dumps(dict_doc)

        # We dump then load with json to use real scalar dict.
        # If not, yaml dump dict-like objects
        clean_dict_doc = json.loads(json_doc)
        return yaml.dump(clean_dict_doc, default_flow_style=False)

    def save_in_file(
        self,
        hapic: "Hapic",
        doc_file_path: str,
        controllers: typing.List[DecoratedController],
        context: ContextInterface,
        title: str = "",
        description: str = "",
    ) -> None:
        doc_yaml = self.get_doc_yaml(
            hapic, controllers=controllers, context=context, title=title, description=description
        )
        with open(doc_file_path, "w+") as doc_file:
            doc_file.write(doc_yaml)
