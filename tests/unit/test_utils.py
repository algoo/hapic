# coding: utf-8
import pytest

from hapic.exception import NotLowercaseCaseException
from hapic.util import LowercaseKeysDict


class TestUtils(object):
    def test_unit__get__ok__nominal_case(self):
        lowercase_dict = LowercaseKeysDict([("foo", "bar")])
        assert "bar" == lowercase_dict.get("foo")
        assert "bar" == lowercase_dict.get("FOO")

    def test_unit__by_key__ok__nominal_case(self):
        lowercase_dict = LowercaseKeysDict([("foo", "bar")])
        assert "bar" == lowercase_dict["foo"]
        assert "bar" == lowercase_dict["FOO"]

    def test_unit__in__ok__nominal_case(self):
        lowercase_dict = LowercaseKeysDict([("foo", "bar")])
        assert "foo" in lowercase_dict
        assert "FOO" in lowercase_dict

    def test_unit__del__ok__nominal_case(self):
        lowercase_dict = LowercaseKeysDict([("foo", "bar")])
        del lowercase_dict["FOO"]

    def test_unit__create__ok__nominal_case(self):
        lowercase_dict = LowercaseKeysDict([("foo", "bar")])
        assert {"foo": "bar"} == lowercase_dict

    def test_unit__create__error__refuse_key(self):
        with pytest.raises(NotLowercaseCaseException):
            LowercaseKeysDict([("FOO", "bar")])

    def test_unit__set__error__refuse_key(self):
        lowercase_dict = LowercaseKeysDict()

        with pytest.raises(NotLowercaseCaseException):
            lowercase_dict.setdefault("FOO", "bar")

    def test_unit__update__error__refuse_key(self):
        lowercase_dict = LowercaseKeysDict()

        with pytest.raises(NotLowercaseCaseException):
            lowercase_dict.update({"FOO": "bar"})
