# -*- coding: utf-8 -*-

try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus


class Base(object):
    pass

