# -*- coding: utf-8 -*-
import sys

import pytest

try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus


class Base(object):
    pass

serpyco_compatible_python = pytest.mark.skipif(sys.version_info < (3, 6), reason="serpyco dataclasses required python>3.6")
