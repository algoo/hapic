# coding: utf-8
from hapic.util import LowercaseDictKeys


class TestUtils(object):
    def test_unit__get__ok__nominal_case(self):
        lowercase_dict = LowercaseDictKeys([("foo", "bar")])
        assert "bar" == lowercase_dict.get("foo")
        assert "bar" == lowercase_dict.get("FOO")

    def test_unit__by_key__ok__nominal_case(self):
        lowercase_dict = LowercaseDictKeys([("foo", "bar")])
        assert "bar" == lowercase_dict["foo"]
        assert "bar" == lowercase_dict["FOO"]

    def test_unit__in__ok__nominal_case(self):
        lowercase_dict = LowercaseDictKeys([("foo", "bar")])
        assert "foo" in lowercase_dict
        assert "FOO" in lowercase_dict

    def test_unit__del__ok__nominal_case(self):
        lowercase_dict = LowercaseDictKeys([("foo", "bar")])
        del lowercase_dict["FOO"]
