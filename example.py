# -*- coding: utf-8 -*-
import marshmallow


class HelloResponseSchema(marshmallow.Schema):
    sentence = marshmallow.fields.String(required=True)
    name = marshmallow.fields.String(required=True)
    color = marshmallow.fields.String(required=False)


class HelloPathSchema(marshmallow.Schema):
    name = marshmallow.fields.String(required=True)


class HelloJsonSchema(marshmallow.Schema):
    color = marshmallow.fields.String(required=True)
