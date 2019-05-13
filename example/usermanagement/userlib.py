# -*- coding: utf-8 -*-

"""
This module implements a basic User management library
"""
import cgi
import os

from aiohttp.web_request import FileField
from bottle import FileUpload
from werkzeug.datastructures import FileStorage


class User(object):
    def __init__(
        self,
        id: int = 0,
        first_name: str = "first",
        last_name: str = "last",
        email_address: str = "",
        company: str = "",
        avatar_path: str = None,
    ):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email_address = email_address
        self.company = company
        self.avatar_path = avatar_path

    @property
    def display_name(self):
        return "{} {}".format(self.first_name, self.last_name)


class UserNotFound(Exception):
    pass


class UserAvatarNotFound(Exception):
    pass


class UserLib(object):
    """
    A dummy library to list, add and delete users
    """

    USERS = []

    def add_user(self, user: User) -> User:
        user.id = 1 + max(u.id for u in UserLib.USERS)
        UserLib.USERS.append(user)
        return user

    def del_user(self, user_id: int) -> None:
        try:
            UserLib.USERS.pop(user_id - 1)
        except:  # noqa: E722
            raise UserNotFound

    def get_user(self, user_id: int) -> User:
        try:
            return UserLib.USERS[user_id - 1]
        except:  # noqa: E722
            raise UserNotFound

    def get_users(self) -> [User]:
        return UserLib.USERS

    def get_user_avatar_path(self, user_id: int):
        try:
            avatar_path = UserLib.USERS[user_id - 1].avatar_path
        except Exception:
            raise UserNotFound

        if not avatar_path:
            raise UserAvatarNotFound()
        return avatar_path

    def update_user_avatar(self, user_id: int, avatar):
        try:
            user = UserLib.USERS[user_id - 1]
        except Exception:
            raise UserNotFound
        if avatar.filename:
            fn = os.path.basename(avatar.filename)
            avatar_path = user_avatar_base_path + fn
            if isinstance(avatar, cgi.FieldStorage):
                # pyramid
                open(avatar_path, "wb").write(avatar.file.read())
            elif isinstance(avatar, FileField):
                # aiohttp
                open(avatar_path, "wb").write(avatar.file.read())
            elif isinstance(avatar, FileUpload):
                # bottle
                open(avatar_path, "wb").write(avatar.file.read())
            elif isinstance(avatar, FileStorage):
                # Flask
                open(avatar_path, "wb").write(avatar.stream.read())
            user.avatar_path = avatar_path
        else:
            raise UserAvatarNotFound()


user_avatar_base_path = "/tmp/"

UserLib.USERS.append(
    User(
        **{
            "id": 1,
            "first_name": "Damien",
            "last_name": "Accorsi",
            "email_address": "damien.accorsi@algoo.fr",
            "company": "Algoo",
            "avatar_path": None,
        }
    )
)
