# -*- coding: utf-8 -*-
import sys

from tests.fixtures import *

collect_ignore = []
if sys.version_info < (3, 6):
    collect_ignore.append(
        "func/fake_api/test_fake_api_aiohttp_serpyco.py"
    )
