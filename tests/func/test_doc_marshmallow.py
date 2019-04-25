# coding: utf-8
from http import HTTPStatus

import marshmallow
from marshmallow.validate import OneOf

from hapic import Hapic
from hapic import MarshmallowProcessor
from hapic.ext.agnostic.context import AgnosticApp
from hapic.ext.agnostic.context import AgnosticContext
from tests.base import Base


class TestDocGeneration(Base):
    """
    Test doc generation for marshmallow with AgnosticContext
    """

    def test_func__input_files_doc__ok__one_file(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MySchema(marshmallow.Schema):
            file_abc = marshmallow.fields.Raw(required=True)

        @hapic.with_api_doc()
        @hapic.input_files(MySchema())
        def my_controller(hapic_data=None):
            assert hapic_data
            assert hapic_data.files

        app.route("/upload", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        assert doc
        assert "/upload" in doc["paths"]
        assert "consumes" in doc["paths"]["/upload"]["post"]
        assert "multipart/form-data" in doc["paths"]["/upload"]["post"]["consumes"]
        assert "parameters" in doc["paths"]["/upload"]["post"]
        assert {"name": "file_abc", "required": True, "in": "formData", "type": "file"} in doc[
            "paths"
        ]["/upload"]["post"]["parameters"]

    def test_func__input_files_doc__ok__two_file(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MySchema(marshmallow.Schema):
            file_abc = marshmallow.fields.Raw(required=True)
            file_def = marshmallow.fields.Raw(required=False)

        @hapic.with_api_doc()
        @hapic.input_files(MySchema())
        def my_controller(hapic_data=None):
            assert hapic_data
            assert hapic_data.files

        app.route("/upload", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        assert doc
        assert "/upload" in doc["paths"]
        assert "consumes" in doc["paths"]["/upload"]["post"]
        assert "multipart/form-data" in doc["paths"]["/upload"]["post"]["consumes"]
        assert "parameters" in doc["paths"]["/upload"]["post"]
        assert {"name": "file_abc", "required": True, "in": "formData", "type": "file"} in doc[
            "paths"
        ]["/upload"]["post"]["parameters"]
        assert {"name": "file_def", "required": False, "in": "formData", "type": "file"} in doc[
            "paths"
        ]["/upload"]["post"]["parameters"]

    def test_func__output_file_doc__ok__nominal_case(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        @hapic.with_api_doc()
        @hapic.output_file(["image/jpeg"])
        def my_controller():
            return b"101010100101"

        app.route("/avatar", method="GET", callback=my_controller)
        doc = hapic.generate_doc()

        assert doc
        assert "/avatar" in doc["paths"]
        assert "produces" in doc["paths"]["/avatar"]["get"]
        assert "image/jpeg" in doc["paths"]["/avatar"]["get"]["produces"]
        assert "200" in doc["paths"]["/avatar"]["get"]["responses"]

    def test_func__input_files_doc__ok__one_file_and_text(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MySchema(marshmallow.Schema):
            name = marshmallow.fields.String(required=True)

        class MyFilesSchema(marshmallow.Schema):
            file_abc = marshmallow.fields.Raw(required=True)

        @hapic.with_api_doc()
        @hapic.input_files(MyFilesSchema())
        @hapic.input_body(MySchema())
        def my_controller(hapic_data=None):
            assert hapic_data
            assert hapic_data.files

        app.route("/upload", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        assert doc
        assert "/upload" in doc["paths"]
        assert "consumes" in doc["paths"]["/upload"]["post"]
        assert "multipart/form-data" in doc["paths"]["/upload"]["post"]["consumes"]
        assert "parameters" in doc["paths"]["/upload"]["post"]
        assert {"name": "file_abc", "required": True, "in": "formData", "type": "file"} in doc[
            "paths"
        ]["/upload"]["post"]["parameters"]

    def test_func__docstring__ok__simple_case(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        @hapic.with_api_doc()
        def my_controller(hapic_data=None):
            """
            Hello doc
            """
            assert hapic_data
            assert hapic_data.files

        app.route("/upload", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        assert doc.get("paths")
        assert "/upload" in doc["paths"]
        assert "post" in doc["paths"]["/upload"]
        assert "description" in doc["paths"]["/upload"]["post"]
        assert "Hello doc" == doc["paths"]["/upload"]["post"]["description"]

    def test_func__tags__ok__nominal_case(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        @hapic.with_api_doc(tags=["foo", "bar"])
        def my_controller(hapic_data=None):
            assert hapic_data
            assert hapic_data.files

        app.route("/upload", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        assert doc.get("paths")
        assert "/upload" in doc["paths"]
        assert "post" in doc["paths"]["/upload"]
        assert "tags" in doc["paths"]["/upload"]["post"]
        assert ["foo", "bar"] == doc["paths"]["/upload"]["post"]["tags"]

    def test_func__errors__nominal_case(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        @hapic.with_api_doc()
        @hapic.handle_exception()
        def my_controller(hapic_data=None):
            assert hapic_data

        app.route("/upload", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        assert doc.get("paths")
        assert "/upload" in doc["paths"]
        assert "post" in doc["paths"]["/upload"]
        assert "responses" in doc["paths"]["/upload"]["post"]
        assert "500" in doc["paths"]["/upload"]["post"]["responses"]
        assert {
            "description": Exception.__doc__,
            "schema": {"$ref": "#/definitions/DefaultErrorSchema"},
        } == doc["paths"]["/upload"]["post"]["responses"]["500"]

    def test_func__errors__explicit_description(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        @hapic.with_api_doc()
        @hapic.handle_exception(description="Any Exception")
        def my_controller(hapic_data=None):
            assert hapic_data

        app.route("/upload", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        assert doc.get("paths")
        assert "/upload" in doc["paths"]
        assert "post" in doc["paths"]["/upload"]
        assert "responses" in doc["paths"]["/upload"]["post"]
        assert "500" in doc["paths"]["/upload"]["post"]["responses"]
        assert {
            "description": "Any Exception",
            "schema": {"$ref": "#/definitions/DefaultErrorSchema"},
        } == doc["paths"]["/upload"]["post"]["responses"]["500"]

    def test_func__errors__docstring_exception(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MyException(Exception):
            "Just a docstring"

        @hapic.with_api_doc()
        @hapic.handle_exception(description="Just a docstring")
        def my_controller(hapic_data=None):
            assert hapic_data

        app.route("/upload", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        assert doc.get("paths")
        assert "/upload" in doc["paths"]
        assert "post" in doc["paths"]["/upload"]
        assert "responses" in doc["paths"]["/upload"]["post"]
        assert "500" in doc["paths"]["/upload"]["post"]["responses"]
        assert {
            "description": "Just a docstring",
            "schema": {"$ref": "#/definitions/DefaultErrorSchema"},
        } == doc["paths"]["/upload"]["post"]["responses"]["500"]

    def test_func__errors__http_status_description(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MyException(Exception):
            pass

        @hapic.with_api_doc()
        @hapic.handle_exception(MyException, http_code=HTTPStatus.BAD_REQUEST)
        def my_controller(hapic_data=None):
            assert hapic_data

        app.route("/upload", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        assert doc.get("paths")
        assert "/upload" in doc["paths"]
        assert "post" in doc["paths"]["/upload"]
        assert "responses" in doc["paths"]["/upload"]["post"]
        assert "400" in doc["paths"]["/upload"]["post"]["responses"]
        assert {
            "description": "BAD_REQUEST: Bad request syntax or unsupported method",
            "schema": {"$ref": "#/definitions/DefaultErrorSchema"},
        } == doc["paths"]["/upload"]["post"]["responses"]["400"]

    def test_func__errors__http_status_as_int_description(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MyException(Exception):
            pass

        @hapic.with_api_doc()
        @hapic.handle_exception(MyException, http_code=400)
        def my_controller(hapic_data=None):
            assert hapic_data

        app.route("/upload", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        assert doc.get("paths")
        assert "/upload" in doc["paths"]
        assert "post" in doc["paths"]["/upload"]
        assert "responses" in doc["paths"]["/upload"]["post"]
        assert "400" in doc["paths"]["/upload"]["post"]["responses"]
        assert {
            "description": "400",
            "schema": {"$ref": "#/definitions/DefaultErrorSchema"},
        } == doc["paths"]["/upload"]["post"]["responses"]["400"]

    def test_func__errors__multiple_same_http_status_description(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MyFirstException(Exception):
            pass

        class MySecondException(Exception):
            "Just a docstring"

        class MyThirdException(Exception):
            "Docstring not used"
            pass

        class MyFourthException(Exception):
            pass

        @hapic.with_api_doc()
        @hapic.handle_exception(MyFirstException, http_code=HTTPStatus.BAD_REQUEST)
        @hapic.handle_exception(MySecondException, http_code=HTTPStatus.BAD_REQUEST)
        @hapic.handle_exception(
            MyThirdException, http_code=HTTPStatus.BAD_REQUEST, description="explicit description"
        )
        @hapic.handle_exception(MyFourthException, http_code=400)
        def my_controller(hapic_data=None):
            assert hapic_data

        app.route("/upload", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        assert doc.get("paths")
        assert "/upload" in doc["paths"]
        assert "post" in doc["paths"]["/upload"]
        assert "responses" in doc["paths"]["/upload"]["post"]
        assert "400" in doc["paths"]["/upload"]["post"]["responses"]
        assert "description"

        assert doc["paths"]["/upload"]["post"]["responses"]["400"]["description"]
        descriptions = doc["paths"]["/upload"]["post"]["responses"]["400"]["description"].split(
            "\n\n"
        )
        assert "BAD_REQUEST: Bad request syntax or unsupported method" in descriptions
        assert "explicit description" in descriptions
        assert "400" in descriptions
        assert "Just a docstring" in descriptions
        assert "Docstring not used" not in descriptions
        assert doc["paths"]["/upload"]["post"]["responses"]["400"]["schema"]
        assert {"$ref": "#/definitions/DefaultErrorSchema"} == doc["paths"]["/upload"]["post"][
            "responses"
        ]["400"]["schema"]

    def test_func__enum__nominal_case(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MySchema(marshmallow.Schema):
            category = marshmallow.fields.String(validate=OneOf(["foo", "bar"]))

        @hapic.with_api_doc()
        @hapic.input_body(MySchema())
        def my_controller():
            return

        app.route("/paper", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        assert ["foo", "bar"] == doc.get("definitions", {}).get("MySchema", {}).get(
            "properties", {}
        ).get("category", {}).get("enum")

    def test_func__schema_in_doc__ok__nominal_case(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MySchema(marshmallow.Schema):
            name = marshmallow.fields.String(required=True)

        @hapic.with_api_doc()
        @hapic.input_body(MySchema())
        def my_controller():
            return {"name": "test"}

        app.route("/paper", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        assert doc.get("definitions", {}).get("MySchema", {})
        schema_def = doc.get("definitions", {}).get("MySchema", {})
        assert schema_def.get("properties", {}).get("name", {}).get("type")

        assert doc.get("paths").get("/paper").get("post").get("parameters")[0]
        schema_ref = doc.get("paths").get("/paper").get("post").get("parameters")[0]
        assert schema_ref.get("in") == "body"
        assert schema_ref.get("name") == "body"
        assert schema_ref["schema"]["$ref"] == "#/definitions/MySchema"

    def test_func__schema_in_doc__ok__many_case(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MySchema(marshmallow.Schema):
            name = marshmallow.fields.String(required=True)

        @hapic.with_api_doc()
        @hapic.input_body(MySchema(many=True))
        def my_controller():
            return {"name": "test"}

        app.route("/paper", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        assert doc.get("definitions", {}).get("MySchema", {})
        schema_def = doc.get("definitions", {}).get("MySchema", {})
        assert schema_def.get("properties", {}).get("name", {}).get("type")

        assert doc.get("paths").get("/paper").get("post").get("parameters")[0]
        schema_ref = doc.get("paths").get("/paper").get("post").get("parameters")[0]
        assert schema_ref.get("in") == "body"
        assert schema_ref.get("name") == "body"
        assert schema_ref["schema"] == {
            "items": {"$ref": "#/definitions/MySchema"},
            "type": "array",
        }

    def test_func__schema_in_doc__ok__exclude_case(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MySchema(marshmallow.Schema):
            name = marshmallow.fields.String(required=True)
            name2 = marshmallow.fields.String(required=True)

        @hapic.with_api_doc()
        @hapic.input_body(MySchema(exclude=("name2",)))
        def my_controller():
            return {"name": "test"}

        app.route("/paper", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        definitions = doc.get("definitions", {})
        # TODO - G-M - Find better way to find our new schema
        # Do Better test when we were able to set correctly schema name
        # according to content
        schema_name = None
        for elem in definitions.keys():
            if elem != "MySchema":
                schema_name = elem
                break
        assert schema_name
        schema_def = definitions[schema_name]
        assert schema_def.get("properties", {}).get("name", {}).get("type") == "string"
        assert doc.get("paths").get("/paper").get("post").get("parameters")[0]
        schema_ref = doc.get("paths").get("/paper").get("post").get("parameters")[0]
        assert schema_ref.get("in") == "body"
        assert schema_ref["schema"]["$ref"] == "#/definitions/{}".format(schema_name)

        @hapic.with_api_doc()
        @hapic.input_body(MySchema(only=("name",)))
        def my_controller():
            return {"name": "test"}

        app.route("/paper", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        # TODO - G-M - Find better way to find our new schema
        # Do Better test when we were able to set correctly schema name
        # according to content
        definitions = doc.get("definitions", {})
        schema_name = None
        for elem in definitions.keys():
            if elem != "MySchema":
                schema_name = elem
                break
        assert schema_name
        schema_def = definitions[schema_name]
        assert schema_def.get("properties", {}).get("name", {}).get("type") == "string"
        assert doc.get("paths").get("/paper").get("post").get("parameters")[0]
        schema_ref = doc.get("paths").get("/paper").get("post").get("parameters")[0]
        assert schema_ref.get("in") == "body"
        assert schema_ref["schema"]["$ref"] == "#/definitions/{}".format(schema_name)

    def test_func__schema_in_doc__ok__many_and_exclude_case(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MySchema(marshmallow.Schema):
            name = marshmallow.fields.String(required=True)
            name2 = marshmallow.fields.String(required=True)

        @hapic.with_api_doc()
        @hapic.input_body(MySchema(exclude=("name2",), many=True))
        def my_controller():
            return {"name": "test"}

        app.route("/paper", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        definitions = doc.get("definitions", {})
        # TODO - G-M - Find better way to find our new schema
        # Do Better test when we were able to set correctly schema name
        # according to content
        schema_name = None
        for elem in definitions.keys():
            if elem != "MySchema":
                schema_name = elem
                break
        assert schema_name
        schema_def = definitions[schema_name]
        assert schema_def.get("properties", {}).get("name", {}).get("type") == "string"
        assert doc.get("paths").get("/paper").get("post").get("parameters")[0]
        schema_ref = doc.get("paths").get("/paper").get("post").get("parameters")[0]
        assert schema_ref.get("in") == "body"
        assert schema_ref["schema"] == {
            "items": {"$ref": "#/definitions/{}".format(schema_name)},
            "type": "array",
        }

    def test_func_schema_in_doc__ok__additionals_fields__file(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MySchema(marshmallow.Schema):
            category = marshmallow.fields.Raw(
                required=True, description="a description", example="00010"
            )

        @hapic.with_api_doc()
        @hapic.input_files(MySchema())
        def my_controller():
            return

        app.route("/upload", method="POST", callback=my_controller)
        doc = hapic.generate_doc()
        assert doc
        assert "/upload" in doc["paths"]
        assert "consumes" in doc["paths"]["/upload"]["post"]
        assert "multipart/form-data" in doc["paths"]["/upload"]["post"]["consumes"]
        assert doc.get("paths").get("/upload").get("post").get("parameters")[0]
        field = doc.get("paths").get("/upload").get("post").get("parameters")[0]
        assert field["description"] == "a description\n\n*example value: 00010*"
        # INFO - G.M - 01-06-2018 - Field example not allowed here,
        # added in description instead
        assert "example" not in field
        assert field["in"] == "formData"
        assert field["type"] == "file"
        assert field["required"] is True

    def test_func_schema_in_doc__ok__additionals_fields__forms__string(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MySchema(marshmallow.Schema):
            category = marshmallow.fields.String(
                required=True,
                description="a description",
                example="00010",
                format="binary",
                enum=["01000", "11111"],
                maxLength=5,
                minLength=5,
                # Theses none string specific parameters should disappear
                # in query/path
                maximum=400,
                # exclusiveMaximun=False,
                # minimum=0,
                # exclusiveMinimum=True,
                # multipleOf=1,
            )

        @hapic.with_api_doc()
        @hapic.input_forms(MySchema())
        def my_controller():
            return

        app.route("/paper", method="POST", callback=my_controller)
        doc = hapic.generate_doc()
        assert "multipart/form-data" in doc["paths"]["/paper"]["post"]["consumes"]
        assert doc.get("paths").get("/paper").get("post").get("parameters")[0]
        field = doc.get("paths").get("/paper").get("post").get("parameters")[0]
        assert field["description"] == "a description\n\n*example value: 00010*"
        # INFO - G.M - 01-06-2018 - Field example not allowed here,
        # added in description instead
        assert "example" not in field
        assert field["format"] == "binary"
        assert field["in"] == "formData"
        assert field["type"] == "string"
        assert field["maxLength"] == 5
        assert field["minLength"] == 5
        assert field["required"] is True
        assert field["enum"] == ["01000", "11111"]
        assert "maximum" not in field

    def test_func_schema_in_doc__ok__additionals_fields__query__string(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MySchema(marshmallow.Schema):
            category = marshmallow.fields.String(
                required=True,
                description="a description",
                example="00010",
                format="binary",
                enum=["01000", "11111"],
                maxLength=5,
                minLength=5,
                # Theses none string specific parameters should disappear
                # in query/path
                maximum=400,
                # exclusiveMaximun=False,
                # minimum=0,
                # exclusiveMinimum=True,
                # multipleOf=1,
            )

        @hapic.with_api_doc()
        @hapic.input_query(MySchema())
        def my_controller():
            return

        app.route("/paper", method="POST", callback=my_controller)
        doc = hapic.generate_doc()
        assert doc.get("paths").get("/paper").get("post").get("parameters")[0]
        field = doc.get("paths").get("/paper").get("post").get("parameters")[0]
        assert field["description"] == "a description\n\n*example value: 00010*"
        # INFO - G.M - 01-06-2018 - Field example not allowed here,
        # added in description instead
        assert "example" not in field
        assert field["format"] == "binary"
        assert field["in"] == "query"
        assert field["type"] == "string"
        assert field["maxLength"] == 5
        assert field["minLength"] == 5
        assert field["required"] is True
        assert field["enum"] == ["01000", "11111"]
        assert "maximum" not in field

    def test_func_schema_in_doc__ok__additionals_fields__path__string(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MySchema(marshmallow.Schema):
            category = marshmallow.fields.String(
                required=True,
                description="a description",
                example="00010",
                format="binary",
                enum=["01000", "11111"],
                maxLength=5,
                minLength=5,
                # Theses none string specific parameters should disappear
                # in query/path
                maximum=400,
                # exclusiveMaximun=False,
                # minimum=0,
                # exclusiveMinimum=True,
                # multipleOf=1,
            )

        @hapic.with_api_doc()
        @hapic.input_path(MySchema())
        def my_controller():
            return

        app.route("/paper", method="POST", callback=my_controller)
        doc = hapic.generate_doc()
        assert doc.get("paths").get("/paper").get("post").get("parameters")[0]
        field = doc.get("paths").get("/paper").get("post").get("parameters")[0]
        assert field["description"] == "a description\n\n*example value: 00010*"
        # INFO - G.M - 01-06-2018 - Field example not allowed here,
        # added in description instead
        assert "example" not in field
        assert field["format"] == "binary"
        assert field["in"] == "path"
        assert field["type"] == "string"
        assert field["maxLength"] == 5
        assert field["minLength"] == 5
        assert field["required"] is True
        assert field["enum"] == ["01000", "11111"]
        assert "maximum" not in field

    def test_func_schema_in_doc__ok__additionals_fields__path__number(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MySchema(marshmallow.Schema):
            category = marshmallow.fields.Integer(
                required=True,
                description="a number",
                example="12",
                format="int64",
                enum=[4, 6],
                # Theses none string specific parameters should disappear
                # in query/path
                maximum=14,
                exclusiveMaximun=False,
                minimum=0,
                exclusiveMinimum=True,
                multipleOf=2,
            )

        @hapic.with_api_doc()
        @hapic.input_path(MySchema())
        def my_controller():
            return

        app.route("/paper", method="POST", callback=my_controller)
        doc = hapic.generate_doc()
        assert doc.get("paths").get("/paper").get("post").get("parameters")[0]
        field = doc.get("paths").get("/paper").get("post").get("parameters")[0]
        assert field["description"] == "a number\n\n*example value: 12*"
        # INFO - G.M - 01-06-2018 - Field example not allowed here,
        # added in description instead
        assert "example" not in field
        assert field["format"] == "int64"
        assert field["in"] == "path"
        assert field["type"] == "integer"
        assert field["maximum"] == 14
        assert field["minimum"] == 0
        assert field["exclusiveMinimum"] is True
        assert field["required"] is True
        assert field["enum"] == [4, 6]
        assert field["multipleOf"] == 2

    def test_func_schema_in_doc__ok__additionals_fields__body__number(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MySchema(marshmallow.Schema):
            category = marshmallow.fields.Integer(
                required=True,
                description="a number",
                example="12",
                format="int64",
                enum=[4, 6],
                # Theses none string specific parameters should disappear
                # in query/path
                maximum=14,
                exclusiveMaximun=False,
                minimum=0,
                exclusiveMinimum=True,
                multipleOf=2,
            )

        @hapic.with_api_doc()
        @hapic.input_body(MySchema())
        def my_controller():
            return

        app.route("/paper", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        schema_field = (
            doc.get("definitions", {}).get("MySchema", {}).get("properties", {}).get("category", {})
        )
        assert schema_field
        assert schema_field["description"] == "a number"
        assert schema_field["example"] == "12"
        assert schema_field["format"] == "int64"
        assert schema_field["type"] == "integer"
        assert schema_field["maximum"] == 14
        assert schema_field["minimum"] == 0
        assert schema_field["exclusiveMinimum"] is True
        assert schema_field["enum"] == [4, 6]
        assert schema_field["multipleOf"] == 2

    def test_func_schema_in_doc__ok__additionals_fields__body__string(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MySchema(marshmallow.Schema):
            category = marshmallow.fields.String(
                required=True,
                description="a description",
                example="00010",
                format="binary",
                enum=["01000", "11111"],
                maxLength=5,
                minLength=5,
            )

        @hapic.with_api_doc()
        @hapic.input_body(MySchema())
        def my_controller():
            return

        app.route("/paper", method="POST", callback=my_controller)
        doc = hapic.generate_doc()

        schema_field = (
            doc.get("definitions", {}).get("MySchema", {}).get("properties", {}).get("category", {})
        )
        assert schema_field
        assert schema_field["description"] == "a description"
        assert schema_field["example"] == "00010"
        assert schema_field["format"] == "binary"
        assert schema_field["type"] == "string"
        assert schema_field["maxLength"] == 5
        assert schema_field["minLength"] == 5
        assert schema_field["enum"] == ["01000", "11111"]

    def test_func__schema_with_many__ok__with_exclude(self):
        hapic = Hapic(processor_class=MarshmallowProcessor)
        app = AgnosticApp()
        hapic.set_context(AgnosticContext(app=app))

        class MySchema(marshmallow.Schema):
            first_name = marshmallow.fields.String(required=True)
            last_name = marshmallow.fields.String(required=False)

        @hapic.with_api_doc()
        @hapic.output_body(MySchema(many=True, exclude=("last_name",)))
        def my_controller(hapic_data=None):
            pass

        app.route("/", method="GET", callback=my_controller)
        doc = hapic.generate_doc()

        assert {
            "MySchema_without_last_name": {
                "type": "object",
                "properties": {"first_name": {"type": "string"}},
                "required": ["first_name"],
            }
        } == doc["definitions"]
