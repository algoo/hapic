import dataclasses

import flask
import serpyco
import pytest

import hapic
from hapic.ext.flask import FlaskContext
from hapic.processor.serpyco import SerpycoProcessor

@pytest.fixture
def flask_app() -> flask.Flask:
    app = flask.Flask("test_flask")
    h = hapic.Hapic(SerpycoProcessor)
    h.set_context(FlaskContext(app))

    @dataclasses.dataclass
    class InputPath:
        resource_id : int


    @app.get("/resources/<int:resource_id>")
    @h.input_path(InputPath)
    def get_resource(resource_id: int, hapic_data: hapic.HapicData) -> str:
        return str(hapic_data.path.resource_id)

    return app

class TestFlaskExt:
    def test_unit__request_parameters__ok__nominal_case(self, flask_app: flask.Flask) -> None:
        client = flask_app.test_client()
        assert client.get("/resources/23").text == "23"
