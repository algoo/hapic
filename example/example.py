# -*- coding: utf-8 -*-
import marshmallow


class ErrorResponseSchema(marshmallow.Schema):
    message = marshmallow.fields.String(required=True)
    details = marshmallow.fields.Dict(required=True)


class HelloResponseSchema(marshmallow.Schema):
    sentence = marshmallow.fields.String(required=True)
    name = marshmallow.fields.String(required=True)
    color = marshmallow.fields.String(required=False)


class HelloPathSchema(marshmallow.Schema):
    name = marshmallow.fields.String(required=True, validate=marshmallow.validate.Length(min=3))


class HelloQuerySchema(marshmallow.Schema):
    alive = marshmallow.fields.Boolean(required=False)


class HelloJsonSchema(marshmallow.Schema):
    color = marshmallow.fields.String(required=True, validate=marshmallow.validate.Length(min=3))


class HelloFileSchema(marshmallow.Schema):
    myfile = marshmallow.fields.Raw(required=True)
