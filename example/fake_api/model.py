# -*- coding: utf-8 -*-


class User(object):
    def __init__(
        self,
        id: int,
        username: str,
        display_name: str,
        company: str,
        email_address: str = "",
        first_name: str = "",
        last_name: str = "",
    ) -> None:
        self.id = id
        self.username = username
        self.email_address = email_address
        self.first_name = first_name
        self.last_name = last_name
        self.display_name = display_name
        self.company = company
