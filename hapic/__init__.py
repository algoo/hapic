# -*- coding: utf-8 -*-
from hapic.hapic import Hapic
from hapic.data import HapicData
from hapic import ext

_hapic_default = Hapic()

with_api_doc = _hapic_default.with_api_doc
input_headers = _hapic_default.input_headers
input_body = _hapic_default.input_body
input_path = _hapic_default.input_path
input_query = _hapic_default.input_query
input_forms = _hapic_default.input_forms
output_headers = _hapic_default.output_headers
output_body = _hapic_default.output_body
generate_doc = _hapic_default.generate_doc
set_context = _hapic_default.set_context
handle_exception = _hapic_default.handle_exception
