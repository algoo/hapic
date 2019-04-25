# coding: utf-8
from aiohttp import web
import marshmallow

from hapic import Hapic
from hapic import HapicData
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
from hapic.ext.aiohttp.context import AiohttpContext

hapic = Hapic(async_=True)


class DisplayNameInputPathSchema(marshmallow.Schema):
    name = marshmallow.fields.String(required=False, allow_none=True)


class DisplayBodyInputBodySchema(marshmallow.Schema):
    foo = marshmallow.fields.String(required=True)


class DisplayBodyOutputBodySchema(marshmallow.Schema):
    data = marshmallow.fields.Dict(required=True)


@hapic.with_api_doc()
@hapic.input_path(DisplayNameInputPathSchema())
async def display_name(request, hapic_data):
    name = request.match_info.get("name", "Anonymous")
    text = "Hello, " + name
    return web.json_response({"sentence": text})


@hapic.with_api_doc()
@hapic.input_body(DisplayBodyInputBodySchema())
@hapic.output_body(DisplayBodyOutputBodySchema())
async def display_body(request, hapic_data: HapicData):
    data = hapic_data.body
    return {"data": data}


async def do_login(request):
    data = await request.json()
    login = data["login"]

    return web.json_response({"login": login})


app = web.Application(debug=True)
app.add_routes(
    [
        web.get("/n/", display_name),
        web.get("/n/{name}", display_name),
        web.post("/n/{name}", display_name),
        web.post("/b/", display_body),
        web.post("/login", do_login),
    ]
)


hapic.set_context(AiohttpContext(app, default_error_builder=MarshmallowDefaultErrorBuilder()))


# import json
# import yaml
# print(yaml.dump(
#     json.loads(json.dumps(hapic.generate_doc())),
#     default_flow_style=False,
# ))

web.run_app(app)
