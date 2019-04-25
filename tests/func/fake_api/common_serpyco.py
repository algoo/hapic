from collections import OrderedDict

from serpyco import StringFormat

# TODO BS 2018-11-27; Used for test
# tests.func.fake_api.test_fake_api\
#     .test_func__test_fake_api_doc_ok__aiohttp_serpyco
# But must be replaced by atomic testing
serpyco_SWAGGER_DOC_API = {
    "info": {
        "description": "just an example of hapic API",
        "title": "Fake API",
        "version": "1.0.0",
    },
    "paths": OrderedDict(
        [
            (
                "/about",
                {
                    "get": {
                        "responses": {
                            200: {
                                "description": "200",
                                "schema": {"$ref": "#/definitions/AboutResponseSchema"},
                            }
                        },
                        "description": "General information about this API.",
                    }
                },
            ),
            (
                "/users",
                {
                    "get": {
                        "responses": {
                            200: {
                                "description": "200",
                                "schema": {"$ref": "#/definitions/ListsUserSchema"},
                            }
                        },
                        "description": "Obtain users list.",
                    }
                },
            ),
            (
                "/users2",
                {
                    "get": {
                        "responses": {
                            200: {
                                "description": "200",
                                "schema": {
                                    "$ref": "#/definitions/UserSchema_exclude_first_name_last_name_email_address"
                                },
                            }
                        },
                        "description": "Obtain users list.",
                    }
                },
            ),
            (
                "/users/{id}",
                {
                    "get": {
                        "responses": {
                            200: {
                                "description": "200",
                                "schema": {"$ref": "#/definitions/UserSchema"},
                            }
                        },
                        "parameters": [
                            {
                                "type": "integer",
                                "minimum": 1,
                                "in": "path",
                                "name": "id",
                                "required": True,
                            }
                        ],
                        "description": "Obtain one user",
                    },
                    "delete": {
                        "responses": {
                            204: {
                                "description": "204",
                                "schema": {"$ref": "#/definitions/NoContentSchema"},
                            }
                        },
                        "parameters": [
                            {
                                "type": "integer",
                                "minimum": 1,
                                "in": "path",
                                "name": "id",
                                "required": True,
                            }
                        ],
                        "description": "delete user",
                    },
                },
            ),
            (
                "/users/",
                {
                    "post": {
                        "parameters": [
                            {
                                "in": "body",
                                "name": "body",
                                "schema": {"$ref": "#/definitions/UserSchema_exclude_id"},
                            }
                        ],
                        "responses": {
                            200: {
                                "description": "200",
                                "schema": {"$ref": "#/definitions/UserSchema"},
                            }
                        },
                        "description": "Add new user",
                    }
                },
            ),
        ]
    ),
    "tags": [],
    "securityDefinitions": {},
    "swagger": "2.0",
    "parameters": {},
    "responses": {},
    "definitions": {
        "PaginationSchema": {
            "type": "object",
            "properties": {
                "first_id": {"type": "integer"},
                "last_id": {"type": "integer"},
                "current_id": {"type": "integer"},
            },
            "required": ["first_id", "last_id", "current_id"],
            "description": "A docstring to prevent auto generated docstring",
        },
        "UserSchema_exclude_first_name_last_name_email_address": {
            "type": "object",
            "properties": {
                "display_name": {"type": "string"},
                "company": {"type": "string"},
                "username": {"type": "string", "pattern": "[\\w-]+"},
                "id": {"type": "integer"},
            },
            "required": ["company", "display_name", "username"],
            "description": "A docstring to prevent auto generated docstring",
        },
        "ListsUserSchema": {
            "type": "object",
            "properties": {
                "pagination": {"$ref": "#/definitions/PaginationSchema"},
                "item_nb": {"type": "integer", "minimum": 0},
                "items": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/UserSchema_exclude_first_name_last_name_email_address"
                    },
                },
            },
            "required": ["item_nb", "items", "pagination"],
            "description": "A docstring to prevent auto generated docstring",
        },
        "UserSchema_exclude_id": {
            "type": "object",
            "properties": {
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "display_name": {"type": "string"},
                "company": {"type": "string"},
                "username": {"type": "string", "pattern": "[\\w-]+"},
                "email_address": {"type": "string", "format": StringFormat.EMAIL},
            },
            "required": [
                "company",
                "display_name",
                "email_address",
                "first_name",
                "last_name",
                "username",
            ],
            "description": "A docstring to prevent auto generated docstring",
        },
        "NoContentSchema": {
            "type": "object",
            "properties": {},
            "description": "A docstring to prevent auto generated docstring",
        },
        "UserSchema": {
            "type": "object",
            "properties": {
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "display_name": {"type": "string"},
                "company": {"type": "string"},
                "username": {"type": "string", "pattern": "[\\w-]+"},
                "email_address": {"type": "string", "format": StringFormat.EMAIL},
                "id": {"type": "integer"},
            },
            "required": [
                "company",
                "display_name",
                "email_address",
                "first_name",
                "last_name",
                "username",
            ],
            "description": "A docstring to prevent auto generated docstring",
        },
        "AboutResponseSchema": {
            "type": "object",
            "properties": {
                "version": {"type": "string"},
                "datetime": {"type": "string", "format": "date-time"},
            },
            "required": ["datetime", "version"],
            "description": "A docstring to prevent auto generated docstring",
        },
        "UserPathSchema": {
            "type": "object",
            "properties": {"id": {"type": "integer", "minimum": 1}},
            "required": ["id"],
            "description": "A docstring to prevent auto generated docstring",
        },
    },
}
