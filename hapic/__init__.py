# -*- coding: utf-8 -*-
from hapic.hapic import Hapic

_hapic_default = Hapic()

with_api_doc = _hapic_default.with_api_doc
input_headers = _hapic_default.input_headers
input_body = _hapic_default.input_body
input_path = _hapic_default.input_path
input_query = _hapic_default.input_query
input_forms = _hapic_default.input_forms
output_headers = _hapic_default.output_headers
output_body = _hapic_default.output_body
# with_api_doc_bis = _hapic_default.with_api_doc_bis
generate_doc = _hapic_default.generate_doc
handle_exception = _hapic_default.handle_exception

# from hapic.hapic import with_api_doc
# from hapic.hapic import with_api_doc_bis
# from hapic.hapic import generate_doc
# from hapic.hapic import output_body
# from hapic.hapic import input_body
# from hapic.hapic import input_query
# from hapic.hapic import input_path
# from hapic.hapic import input_headers
# from hapic.context import BottleContext
# from hapic.hapic import set_fake_default_context
# from hapic.hapic import error_schema


# class FakeSetContext(object):
#     def bottle_context(self):
#         hapic.set_fake_default_context(BottleContext())
#         def decorator(func):
#             def wrapper(*args, **kwargs):
#                 return func(*args, **kwargs)
#             return wrapper
#         return decorator
#
#
# class FakeExt(object):
#     bottle = FakeSetContext()
#
#
# ext = FakeExt()
