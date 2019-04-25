# -*- coding: utf-8 -*-
from io import BytesIO
import json
from wsgiref.simple_server import make_server

from PIL import Image
from pyramid.config import Configurator

from example import HelloJsonSchema
from example import HelloPathSchema
from example import HelloQuerySchema
from example import HelloResponseSchema
import hapic
from hapic.data import HapicData
from hapic.data import HapicFile
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
from hapic.ext.pyramid import PyramidContext

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
    def hello(self, context, request, hapic_data: HapicData):
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
        name = request.matchdict.get("name", None)
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
    def hello2(self, context, request, hapic_data: HapicData):
        name = request.matchdict.get("name", None)
        return {"sentence": "Hello !", "name": name, "color": hapic_data.body.get("color")}

    kwargs = {"validated_data": {"name": "bob"}, "name": "bob"}

    @hapic.with_api_doc()
    # @hapic.ext.bottle.bottle_context()
    # @hapic.error_schema(ErrorResponseSchema())
    @hapic.input_path(HelloPathSchema())
    @hapic.output_body(HelloResponseSchema())
    def hello3(self, context, request, hapic_data: HapicData):
        name = request.matchdict.get("name", None)
        return {"sentence": "Hello !", "name": name}

    @hapic.with_api_doc()
    @hapic.output_file(["image/jpeg"])
    def hellofile(self, context, request):
        return HapicFile(
            file_path="/home/guenael/Images/Mount_Ararat_and_the_Araratian_plain_(cropped).jpg",
            mimetype="image/jpeg",
            as_attachment=False,
        )

    @hapic.with_api_doc()
    @hapic.output_file(["image/jpeg"])
    def hellofile2(self, context, request):
        file = BytesIO()
        image = Image.new("RGBA", size=(1000, 1000), color=(0, 0, 0))
        image.save(file, "png")
        file.name = "test_image.png"
        file.seek(0)
        return HapicFile(filename="coucou.png", file_object=file, mimetype="image/png")

    @hapic.with_api_doc()
    @hapic.output_file(["image/jpeg"])
    def hellofile3(self, context, request):
        file = BytesIO()
        image = Image.new("RGBA", size=(1000, 1000), color=(0, 0, 0))
        image.save(file, "png")
        file.name = "test_image.png"
        file.seek(0)
        return HapicFile(
            filename="coucou.png", file_object=file, mimetype="image/png", as_attachment=True
        )

    def bind(self, configurator: Configurator):
        configurator.add_route("hello", "/hello/{name}", request_method="GET")
        configurator.add_view(self.hello, route_name="hello", renderer="json")

        configurator.add_route("hello2", "/hello/{name}", request_method="POST")
        configurator.add_view(self.hello2, route_name="hello2", renderer="json")

        configurator.add_route("hello3", "/hello3/{name}", request_method="GET")
        configurator.add_view(self.hello3, route_name="hello3", renderer="json")

        configurator.add_route("hellofile", "/hellofile", request_method="GET")
        configurator.add_view(self.hellofile, route_name="hellofile")

        configurator.add_route("hellofile2", "/hellofile2", request_method="GET")
        configurator.add_view(self.hellofile2, route_name="hellofile2")

        configurator.add_route("hellofile3", "/hellofile3", request_method="GET")
        configurator.add_view(self.hellofile3, route_name="hellofile3")


configurator = Configurator(autocommit=True)
controllers = Controllers()

controllers.bind(configurator)

hapic.set_context(
    PyramidContext(configurator, default_error_builder=MarshmallowDefaultErrorBuilder())
)
print(json.dumps(hapic.generate_doc()))

server = make_server("0.0.0.0", 8080, configurator.make_wsgi_app())
server.serve_forever()
