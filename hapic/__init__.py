# -*- coding: utf-8 -*-
# from hapic.hapic import Hapic

# _hapic_default = Hapic()
#
# with_api_doc = _hapic_default.with_api_doc
# with_api_doc_bis = _hapic_default.with_api_doc_bis
# generate_doc = _hapic_default.generate_doc

from hapic.hapic import with_api_doc
from hapic.hapic import with_api_doc_bis
from hapic.hapic import generate_doc
from hapic.hapic import output
from hapic.hapic import input_body
from hapic.hapic import input_query
from hapic.hapic import input_path
from hapic.hapic import input_headers
from hapic.hapic import BottleContext
from hapic.hapic import set_fake_default_context
from hapic.hapic import error_schema


class FakeSetContext(object):
    def bottle_context(self):
        hapic.set_fake_default_context(BottleContext())
        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator


class FakeExt(object):
    bottle = FakeSetContext()


ext = FakeExt()
