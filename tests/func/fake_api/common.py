from collections import OrderedDict

SWAGGER_DOC_API = {
    "definitions": {
        "AboutResponseSchema": {
            "properties": {
                "datetime": {"format": "date-time", "type": "string"},
                "version": {"type": "string"},
            },
            "required": ["datetime", "version"],
            "type": "object",
        },
        "ListsUserSchema": {
            "properties": {
                "item_nb": {"format": "int32", "minimum": 0, "type": "integer"},
                "items": {
                    "items": {
                        "$ref": "#/definitions/UserSchema_without_email_address_first_name_last_name"
                    },
                    "type": "array",
                },
                "pagination": {"$ref": "#/definitions/PaginationSchema"},
            },
            "required": ["item_nb"],
            "type": "object",
        },
        "NoContentSchema": {"properties": {}, "type": "object"},
        "PaginationSchema": {
            "properties": {
                "current_id": {"format": "int32", "type": "integer"},
                "first_id": {"format": "int32", "type": "integer"},
                "last_id": {"format": "int32", "type": "integer"},
            },
            "required": ["current_id", "first_id", "last_id"],
            "type": "object",
        },
        "UserSchema": {
            "properties": {
                "company": {"type": "string"},
                "display_name": {"type": "string"},
                "email_address": {"format": "email", "type": "string"},
                "first_name": {"type": "string"},
                "id": {"format": "int32", "type": "integer"},
                "last_name": {"type": "string"},
                "username": {"type": "string", "pattern": "[\\w-]+"},
            },
            "required": [
                "company",
                "display_name",
                "email_address",
                "first_name",
                "id",
                "last_name",
                "username",
            ],
            "type": "object",
        },
        "UserSchema_without_id": {
            "properties": {
                "username": {"type": "string", "pattern": "[\\w-]+"},
                "display_name": {"type": "string"},
                "company": {"type": "string"},
                "last_name": {"type": "string"},
                "email_address": {"format": "email", "type": "string"},
                "first_name": {"type": "string"},
            },
            "required": [
                "company",
                "display_name",
                "email_address",
                "first_name",
                "last_name",
                "username",
            ],
            "type": "object",
        },
        "UserSchema_without_email_address_first_name_last_name": {
            "properties": {
                "username": {"type": "string", "pattern": "[\\w-]+"},
                "id": {"format": "int32", "type": "integer"},
                "company": {"type": "string"},
                "display_name": {"type": "string"},
            },
            "required": ["company", "display_name", "id", "username"],
            "type": "object",
        },
    },
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
                        "description": "General information about this API.",
                        "responses": {
                            "200": {
                                "description": "200",
                                "schema": {"$ref": "#/definitions/AboutResponseSchema"},
                            }
                        },
                    }
                },
            ),
            (
                "/users",
                {
                    "get": {
                        "description": "Obtain users list.",
                        "responses": {
                            "200": {
                                "description": "200",
                                "schema": {"$ref": "#/definitions/ListsUserSchema"},
                            }
                        },
                    }
                },
            ),
            (
                "/users/{id}",
                {
                    "delete": {
                        "description": "delete user",
                        "parameters": [
                            {
                                "format": "int32",
                                "minimum": 1,
                                "in": "path",
                                "name": "id",
                                "required": True,
                                "type": "integer",
                            }
                        ],
                        "responses": {
                            "204": {
                                "description": "204",
                                "schema": {"$ref": "#/definitions/NoContentSchema"},
                            }
                        },
                    },
                    "get": {
                        "description": "Obtain one user",
                        "parameters": [
                            {
                                "format": "int32",
                                "in": "path",
                                "minimum": 1,
                                "name": "id",
                                "required": True,
                                "type": "integer",
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "200",
                                "schema": {"$ref": "#/definitions/UserSchema"},
                            }
                        },
                    },
                },
            ),
            (
                "/users/",
                {
                    "post": {
                        "description": "Add new user",
                        "parameters": [
                            {
                                "in": "body",
                                "name": "body",
                                "schema": {"$ref": "#/definitions/UserSchema_without_id"},
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "200",
                                "schema": {"$ref": "#/definitions/UserSchema"},
                            }
                        },
                    }
                },
            ),
            (
                "/users2",
                {
                    "get": {
                        "description": "Obtain users list.",
                        "responses": {
                            "200": {
                                "description": "200",
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "$ref": "#/definitions/UserSchema_without_email_address_first_name_last_name"
                                    },
                                },
                            }
                        },
                    }
                },
            ),
        ]
    ),
    "swagger": "2.0",
}
