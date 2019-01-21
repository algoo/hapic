# -*- coding: utf-8 -*-
import typing

LOGGER_NAME = "hapic"


class LowercaseDictKeys(dict):
    """
    Like a dict but try to use lowercase version of given keys.
    Must give lowercase key to ths dict when fill it.
    """

    def get(
        self, key: typing.Any, default_value: typing.Any = None
    ) -> typing.Any:
        """
        Return value for given key.
        Try with lowercase of given key. If not possible, do with given key.
        """
        try:
            return super().get(key.lower(), default_value)
        except AttributeError:
            return super().get(key, default_value)

    def __contains__(self, key: typing.Any) -> bool:
        """
        True if the dictionary has the specified key, else False.
        Try with lowercase of given key. If not possible, do with given key.
        """
        try:
            return super().__contains__(key.lower())
        except AttributeError:
            return super().__contains__(key)

    def __delitem__(self, key: typing.Any) -> None:
        """
        Delete self[key].
        Try with lowercase of given key. If not possible, do with given key.
        """
        try:
            return super().__delitem__(key.lower())
        except AttributeError:
            return super().__delitem__(key)

    def __getitem__(self, key: typing.Any) -> typing.Any:
        """
        Return value for given key.
        Try with lowercase of given key. If not possible, do with given key.
        """
        try:
            return super().__getitem__(key.lower())
        except AttributeError:
            return super().__getitem__(key)
