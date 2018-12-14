# coding: utf-8
import marshmallow

from hapic.error.main import DefaultErrorBuilder
from hapic.type import TYPE_SCHEMA


class DefaultErrorSchema(marshmallow.Schema):
    message = marshmallow.fields.String(required=True)
    details = marshmallow.fields.Dict(required=False, missing={})
    code = marshmallow.fields.Raw(missing=None)


# FIXME BS 2018-12-06: Marshmallow is used as default by hapic. But
# consequences are a marshmallow dependency. We must resolve that.
# See #124
class MarshmallowDefaultErrorBuilder(DefaultErrorBuilder):
    def get_schema(self) -> TYPE_SCHEMA:
        return DefaultErrorSchema()
