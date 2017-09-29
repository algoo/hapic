# -*- coding: utf-8 -*-
import bottle
import hapic
from example import HelloResponseSchema, HelloPathSchema, HelloJsonSchema
from hapic.hapic import MarshmallowOutputProcessor, BottleContext, \
    MarshmallowPathInputProcessor, MarshmallowJsonInputProcessor


def bob(f):
    def boby(*args, **kwargs):
        return f
    return boby


@hapic.with_api_doc_bis()
@bottle.route('/hello/<name>')
@hapic.input(HelloPathSchema(), MarshmallowPathInputProcessor(), context=BottleContext())  # nopep8
@hapic.output(HelloResponseSchema(), MarshmallowOutputProcessor())
@bob
def hello(name: str):
    return "Hello {}!".format(name)


@hapic.with_api_doc_bis()
@bottle.route('/hello2/<name>')
@hapic.input(HelloPathSchema(), MarshmallowPathInputProcessor(), context=BottleContext())  # nopep8
@hapic.input(HelloJsonSchema(), MarshmallowJsonInputProcessor(), context=BottleContext())  # nopep8
@hapic.output(HelloResponseSchema())
@bob
def hello2(name: str):
    return "Hello {}!".format(name)


@hapic.with_api_doc_bis()
@bottle.route('/hello3/<name>')
@hapic.output(HelloResponseSchema())
def hello3(name: str):
    return "Hello {}!".format(name)

hapic.generate_doc()
bottle.run(host='localhost', port=8080, debug=True)





@bottle.route('/hello/<name>')
@hapic.input_body(HelloPathSchema(), MarshmallowPathInputProcessor(), context=BottleContext())  # nopep8
@hapic.input_header(HelloPathSchema(), MarshmallowPathInputProcessor(), context=BottleContext())  # nopep8
@hapic.input_query(HelloPathSchema(), MarshmallowPathInputProcessor(), context=BottleContext())  # nopep8
@hapic.input_path(HelloPathSchema(), MarshmallowPathInputProcessor(), context=BottleContext())  # nopep8
@hapic.output(HelloResponseSchema(), MarshmallowOutputProcessor())
def hello(name: str, hapic_data):
    return "Hello {}!".format(name)


@hapic.with_api_doc_bis()
@bottle.route('/hello/<name>')
@hapic.input(HelloPathSchema(), MarshmallowPathInputProcessor(), context=BottleContext())  # nopep8
@hapic.output(HelloResponseSchema(), MarshmallowOutputProcessor())
@bob
def hello(name: str):
    return "Hello {}!".format(name)
