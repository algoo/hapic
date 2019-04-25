# -*- coding: utf-8 -*-
import json

import bottle
import yaml

from example.example import HelloFileSchema
from example.example import HelloJsonSchema
from example.example import HelloPathSchema
from example.example import HelloQuerySchema
from example.example import HelloResponseSchema
import hapic
from hapic.data import HapicData
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
from hapic.ext.bottle.context import BottleContext

try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus


def bob(f):
    def boby(*args, **kwargs):
        return f(*args, **kwargs)

    return boby


class Controllers(object):
    @hapic.with_api_doc()
    # @hapic.ext.bottle.bottle_context()
    @hapic.handle_exception(ZeroDivisionError, http_code=HTTPStatus.BAD_REQUEST)
    @hapic.input_path(HelloPathSchema())
    @hapic.input_query(HelloQuerySchema())
    @hapic.output_body(HelloResponseSchema())
    def hello(self, name: str, hapic_data: HapicData):
        """
        my endpoint hello
        ---
        get:
            description: my description
            parameters:
                - in: "path"
                  description: "hello"
                  name: "name"
                  type: "string"
            responses:
                200:
                    description: A pet to be returned
                    schema: HelloResponseSchema
        """
        if name == "zero":
            raise ZeroDivisionError("Don't call him zero !")

        return {"sentence": "Hello !", "name": name}

    @hapic.with_api_doc()
    # @hapic.ext.bottle.bottle_context()
    # @hapic.error_schema(ErrorResponseSchema())
    @hapic.input_path(HelloPathSchema())
    @hapic.input_body(HelloJsonSchema())
    @hapic.output_body(HelloResponseSchema())
    @bob
    def hello2(self, name: str, hapic_data: HapicData):
        return {"sentence": "Hello !", "name": name, "color": hapic_data.body.get("color")}

    kwargs = {"validated_data": {"name": "bob"}, "name": "bob"}

    @hapic.with_api_doc()
    # @hapic.ext.bottle.bottle_context()
    # @hapic.error_schema(ErrorResponseSchema())
    @hapic.input_path(HelloPathSchema())
    @hapic.output_body(HelloResponseSchema())
    def hello3(self, name: str, hapic_data: HapicData):
        return {"sentence": "Hello !", "name": name}

    @hapic.with_api_doc()
    @hapic.input_files(HelloFileSchema())
    @hapic.output_file(["image/jpeg"])
    def hellofile(self, hapic_data: HapicData):
        return hapic_data.files["myfile"]

    def bind(self, app):
        app.route("/hello/<name>", callback=self.hello)
        app.route("/hello/<name>", callback=self.hello2, method="POST")
        app.route("/hello3/<name>", callback=self.hello3)
        app.route("/hellofile", callback=self.hellofile)


app = bottle.Bottle()

controllers = Controllers()
controllers.bind(app)

hapic.set_context(BottleContext(app, default_error_builder=MarshmallowDefaultErrorBuilder()))

print(yaml.dump(json.loads(json.dumps(hapic.generate_doc())), default_flow_style=False))

app.run(host="localhost", port=8080, debug=True)
