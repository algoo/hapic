# -*- coding: utf-8 -*-
import sys

from tests.fixtures import *  # noqa: F403, F401

collect_ignore = []
if sys.version_info < (3, 6):
    collect_ignore.extend(
        [
            "func/fake_api/test_fake_api_aiohttp_serpyco.py",
            "func/test_doc_serpyco.py",
            "unit/test_serpyco_processor.py",
        ]
    )
