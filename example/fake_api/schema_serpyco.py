# -*- coding: utf-8 -*-
import dataclasses
from datetime import datetime
import typing

from serpyco import StringFormat
from serpyco import nested_field
from serpyco import number_field
from serpyco import string_field


@dataclasses.dataclass
class NoContentSchema(object):
    """A docstring to prevent auto generated docstring"""


@dataclasses.dataclass
class AboutResponseSchema(object):
    """A docstring to prevent auto generated docstring"""

    version: str
    datetime: datetime


@dataclasses.dataclass
class UserPathSchema(object):
    """A docstring to prevent auto generated docstring"""

    id: int = number_field(minimum=1, cast_on_load=True)


@dataclasses.dataclass
class UserSchema(object):
    """A docstring to prevent auto generated docstring"""

    first_name: str
    last_name: str
    display_name: str
    company: str
    username: str = string_field(pattern="[\w-]+")  # noqa: W605
    email_address: str = string_field(format_=StringFormat.EMAIL)
    id: typing.Optional[int] = None  # Note: must be optional to be unused in POST user


@dataclasses.dataclass
class PaginationSchema(object):
    """A docstring to prevent auto generated docstring"""

    first_id: int
    last_id: int
    current_id: int


@dataclasses.dataclass
class ListsUserSchema(object):
    """A docstring to prevent auto generated docstring"""

    pagination: PaginationSchema
    item_nb: int = number_field(minimum=0)
    items: typing.List[UserSchema] = nested_field(
        only=["id", "username", "display_name", "company"]
    )
