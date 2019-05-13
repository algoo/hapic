# -*- coding: utf-8 -*-
import marshmallow


class NoContentSchema(marshmallow.Schema):
    pass


class AboutSchema(marshmallow.Schema):
    """ Representation of the /about route """

    version = marshmallow.fields.String(required=True)
    datetime = marshmallow.fields.DateTime(required=True)


class UserIdPathSchema(marshmallow.Schema):
    """
    representation of a user id in the uri. This allow to define rules for
    what is expected. For example, you may want to limit id to number between
    1 and 999
    """

    id = marshmallow.fields.Int(required=True, validate=marshmallow.validate.Range(min=1))


class UserSchema(marshmallow.Schema):
    """Complete representation of a user"""

    id = marshmallow.fields.Int(required=True)
    first_name = marshmallow.fields.String(required=True)
    last_name = marshmallow.fields.String(required=True)
    email_address = marshmallow.fields.Email(required=True)
    display_name = marshmallow.fields.String(required=False)
    company = marshmallow.fields.String(required=False)


class UserDigestSchema(marshmallow.Schema):
    """User representation for listing"""

    id = marshmallow.fields.Int(required=True)
    display_name = marshmallow.fields.String(required=False, default="")


class UserAvatarSchema(marshmallow.Schema):
    """Avatar (image file) of user"""

    avatar = marshmallow.fields.Raw()
