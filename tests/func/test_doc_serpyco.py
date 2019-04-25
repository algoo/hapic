# coding: utf-8
import dataclasses

from hapic import Hapic
from hapic.error.serpyco import SerpycoDefaultErrorBuilder
from hapic.ext.agnostic.context import AgnosticApp
from hapic.ext.agnostic.context import AgnosticContext
from hapic.processor.serpyco import SerpycoProcessor
from tests.base import serpyco_compatible_python


@serpyco_compatible_python
class TestDocSerpyco(object):
    """
    Test doc generation for serpyco with AgnosticContext
    """

    def test_func__ok__doc__exclude_in_processor_output_body(self,):
        app = AgnosticApp()
        hapic = Hapic()
        hapic.set_processor_class(SerpycoProcessor)
        hapic.set_context(AgnosticContext(app, default_error_builder=SerpycoDefaultErrorBuilder()))

        @dataclasses.dataclass
        class UserSchema(object):
            id: int
            name: str
            password: str

        @hapic.with_api_doc()
        @hapic.output_body(UserSchema, processor=SerpycoProcessor(exclude=["password"]))
        def my_view():
            pass

        app.route("/hello", "GET", callback=my_view)
        doc = hapic.generate_doc()

        assert (
            "#/definitions/UserSchema_exclude_password"
            == doc["paths"]["/hello"]["get"]["responses"]["200"]["schema"]["$ref"]
        )
        assert "UserSchema_exclude_password" in doc["definitions"]

    def test_func__ok__doc__exclude_in_processor_input_body(self,):
        app = AgnosticApp()
        hapic = Hapic()
        hapic.set_processor_class(SerpycoProcessor)
        hapic.set_context(AgnosticContext(app, default_error_builder=SerpycoDefaultErrorBuilder()))

        @dataclasses.dataclass
        class UserSchema(object):
            id: int
            name: str
            password: str

        @hapic.with_api_doc()
        @hapic.input_body(UserSchema, processor=SerpycoProcessor(exclude=["password"]))
        def my_view(hapic_data):
            pass

        app.route("/hello", "GET", callback=my_view)
        doc = hapic.generate_doc()

        assert (
            "#/definitions/UserSchema_exclude_password"
            == doc["paths"]["/hello"]["get"]["parameters"][0]["schema"]["$ref"]
        )
        assert "UserSchema_exclude_password" in doc["definitions"]

    def test_func__ok__doc__exclude_in_processor_input_query(self,):
        app = AgnosticApp()
        hapic = Hapic()
        hapic.set_processor_class(SerpycoProcessor)
        hapic.set_context(AgnosticContext(app, default_error_builder=SerpycoDefaultErrorBuilder()))

        @dataclasses.dataclass
        class UserSchema(object):
            id: int
            name: str
            password: str

        @hapic.with_api_doc()
        @hapic.input_query(UserSchema, processor=SerpycoProcessor(exclude=["password"]))
        def my_view(hapic_data):
            pass

        app.route("/hello", "GET", callback=my_view)
        doc = hapic.generate_doc()

        assert 2 == len(doc["paths"]["/hello"]["get"]["parameters"])
        assert "id" == doc["paths"]["/hello"]["get"]["parameters"][0]["name"]
        assert "name" == doc["paths"]["/hello"]["get"]["parameters"][1]["name"]
        assert "UserSchema_exclude_password" in doc["definitions"]

    def test_func__ok__doc__exclude_in_processor_input_path(self,):
        app = AgnosticApp()
        hapic = Hapic()
        hapic.set_processor_class(SerpycoProcessor)
        hapic.set_context(AgnosticContext(app, default_error_builder=SerpycoDefaultErrorBuilder()))

        @dataclasses.dataclass
        class UserSchema(object):
            id: int
            name: str
            password: str

        @hapic.with_api_doc()
        @hapic.input_path(UserSchema, processor=SerpycoProcessor(exclude=["password"]))
        def my_view(hapic_data):
            pass

        app.route("/hello/{id}/{name}", "GET", callback=my_view)
        doc = hapic.generate_doc()

        assert 2 == len(doc["paths"]["/hello/{id}/{name}"]["get"]["parameters"])
        assert "id" == doc["paths"]["/hello/{id}/{name}"]["get"]["parameters"][0]["name"]
        assert "name" == doc["paths"]["/hello/{id}/{name}"]["get"]["parameters"][1]["name"]
        assert "UserSchema_exclude_password" in doc["definitions"]

    def test_func__ok__doc__with_handle_exception(self):
        app = AgnosticApp()
        hapic = Hapic()
        hapic.set_processor_class(SerpycoProcessor)
        hapic.set_context(AgnosticContext(app, default_error_builder=SerpycoDefaultErrorBuilder()))

        @dataclasses.dataclass
        class UserSchema(object):
            id: int
            name: str
            password: str

        @hapic.with_api_doc()
        @hapic.handle_exception(ZeroDivisionError, http_code=400)
        def my_view(hapic_data):
            1 / 0

        app.route("/hello", "GET", callback=my_view)
        doc = hapic.generate_doc()

        assert "DefaultErrorSchema" in doc["definitions"]
        properties = doc["definitions"]["DefaultErrorSchema"]["properties"]
        assert "message" in properties
        assert "details" in properties
        assert "code" in properties
