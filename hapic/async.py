# -*- coding: utf-8 -*-
from hapic.hapic import Hapic

_hapic_default = Hapic(async_=True)

with_api_doc = _hapic_default.with_api_doc
input_headers = _hapic_default.input_headers
input_body = _hapic_default.input_body
input_path = _hapic_default.input_path
input_query = _hapic_default.input_query
input_forms = _hapic_default.input_forms
input_files = _hapic_default.input_files
output_headers = _hapic_default.output_headers
output_body = _hapic_default.output_body
output_file = _hapic_default.output_file
generate_doc = _hapic_default.generate_doc
set_context = _hapic_default.set_context
reset_context = _hapic_default.reset_context
add_documentation_view = _hapic_default.add_documentation_view
handle_exception = _hapic_default.handle_exception
output_stream = _hapic_default.output_stream
