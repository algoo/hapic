# -*- coding: utf-8 -*-

"""
This module implements a basic User management library
"""

class User(object):
    def __init__(
        self,
        id=0,
        first_name='first',
        last_name='last',
        email_address='',
        company=''
    ):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email_address = email_address
        self.company = company

    @property
    def display_name(self):
        return '{} {}'.format(self.first_name, self.last_name)


class UserNotFound(Exception):
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
        except:
            raise UserNotFound

    def get_user(self, user_id: int) -> User:
        try:
            return UserLib.USERS[user_id - 1]
        except:
            raise UserNotFound

    def get_users(self) -> [User]:
        return UserLib.USERS


UserLib.USERS.append(
    User(**{
        'id': 1,
        'first_name': 'Damien',
        'last_name': 'Accorsi',
        'email_address': 'damien.accorsi@algoo.fr',
        'company': 'Algoo',
    }),
)
