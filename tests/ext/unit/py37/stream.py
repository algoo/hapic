# coding: utf-8

"""
This module contains code of python3.7 tests. Python3.7 test code is in
this module because we must import these only when Python > 3.5
"""


def get_func_with_output_stream(hapic, schema):
    @hapic.output_stream(schema())
    async def hello(request):
        yield {"name": "Hello, bob"}
        yield {"name": "Hello, franck"}

    return hello


def get_func_with_output_stream_and_error(hapic, schema, ignore_on_error=True):
    @hapic.output_stream(schema(), ignore_on_error=ignore_on_error)
    async def hello(request):
        yield {"name": "Hello, bob"}
        yield {"nameZ": "Hello, Z"}  # This line is incorrect
        yield {"name": "Hello, franck"}

    return hello
