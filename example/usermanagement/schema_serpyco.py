# -*- coding: utf-8 -*-
import dataclasses
from datetime import datetime
import typing

from serpyco import StringFormat
from serpyco import number_field
from serpyco import string_field


@dataclasses.dataclass
class NoContentSchema(object):
    """A docstring to prevent auto generated docstring"""


@dataclasses.dataclass
class AboutSchema(object):
    """ Representation of the /about route """

    version: str
    datetime: datetime


@dataclasses.dataclass
class UserIdPathSchema(object):
    """
    representation of a user id in the uri. This allow to define rules for
    what is expected. For example, you may want to limit id to number between
    1 and 999
    """

    id: int = number_field(minimum=1, cast_on_load=True)


@dataclasses.dataclass
class UserSchema(object):
    """Complete representation of a user"""

    first_name: str
    last_name: typing.Optional[str]
    display_name: str
    company: typing.Optional[str]
    id: int
    email_address: str = string_field(format_=StringFormat.EMAIL)


@dataclasses.dataclass
class UserDigestSchema(object):
    """User representation for listing"""

    id: int
    display_name: str = ""


@dataclasses.dataclass
class UserAvatarSchema(object):
    """Avatar (image file) of user"""

    avatar: typing.Any
