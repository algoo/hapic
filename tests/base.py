# -*- coding: utf-8 -*-
import sys

import pytest


class Base(object):
    pass


serpyco_compatible_python = pytest.mark.skipif(
    sys.version_info < (3, 6), reason="serpyco dataclasses required python>3.6"
)
