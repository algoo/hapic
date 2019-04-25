# -*- coding: utf-8 -*-
import typing

from hapic.exception import NotLowercaseCaseException

LOGGER_NAME = "hapic"


class LowercaseKeysDict(dict):
    """
    Like a dict but try to use lowercase version of given keys.
    Must give string lowercase key to ths dict when fill it.
    """

    @staticmethod
    def check_key(key: str) -> None:
        try:
            if key.lower() != key:
                raise NotLowercaseCaseException(
                    'Invalid key "{}": must be lowercase str'.format(key)
                )
        except (TypeError, AttributeError):
            raise NotLowercaseCaseException('Invalid key "{}": must be lowercase str'.format(key))

    def __init__(self, seq: typing.Iterable[typing.Tuple[str, typing.Any]] = None) -> None:
        """
        Create dict only if given key lowercase string
        """
        seq = seq or []  # FDV
        seq = seq.items() if isinstance(seq, dict) else seq

        for key, value in iter(seq):
            self.check_key(key)

        super().__init__(seq)

    def get(self, key: str, default_value: typing.Any = None) -> typing.Any:
        """
        Return value for given key.lowercase().
        """
        return super().get(key.lower(), default_value)

    def setdefault(self, key: str, default: typing.Any) -> None:
        self.check_key(key)
        return super().setdefault(key, default)

    def __contains__(self, key: str) -> bool:
        """
        True if the dictionary has the specified key.lowercase(), else False.
        """
        return super().__contains__(key.lower())

    def __delitem__(self, key: str) -> None:
        """
        Delete item for given key.lowercase().
        """
        return super().__delitem__(key.lower())

    def __getitem__(self, key: str) -> typing.Any:
        """
        Return value for given key.lowercase().
        """
        return super().__getitem__(key.lower())

    def __setitem__(self, key, item):
        """
        Set value for given key.lowercase() with given item.
        """
        self.check_key(key)
        super().__setitem__(key, item)

    def has_key(self, key: str):
        """
        Return True if key.lower()
        """
        return key.lower() in self.__dict__

    def update(self, seq: typing.Iterable[typing.Tuple[str, typing.Any]]) -> None:
        seq = seq or []  # FDV
        seq = seq.items() if isinstance(seq, dict) else seq

        for key, value in iter(seq):
            self.check_key(key)

        return super().update(seq)
