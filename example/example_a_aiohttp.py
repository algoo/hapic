# coding: utf-8
import json
import yaml

from aiohttp import web
from hapic import async as hapic
from hapic import async as HapicData
import marshmallow

from hapic.ext.aiohttp.context import AiohttpContext


class HandleInputPath(marshmallow.Schema):
    name = marshmallow.fields.String(
        required=False,
        allow_none=True,
    )


class HandleInputBody(marshmallow.Schema):
    foo = marshmallow.fields.String(
        required=True,
    )


class Handle2OutputBody(marshmallow.Schema):
    data = marshmallow.fields.Dict(
        required=True,
    )


class HandleOutputBody(marshmallow.Schema):
    sentence = marshmallow.fields.String(
        required=True,
    )


@hapic.with_api_doc()
@hapic.input_path(HandleInputPath())
# @hapic.output_body(HandleOutputBody())
async def handle(request, hapic_data):
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.json_response({
        'sentence': text,
    })


@hapic.with_api_doc()
@hapic.input_body(HandleInputBody())
@hapic.output_body(Handle2OutputBody())
async def handle2(request, hapic_data: HapicData):
    data = hapic_data.body
    return {
        'data': data,
    }


async def do_login(request):
    data = await request.json()
    login = data['login']
    password = data['password']

    return web.json_response({
        'login': login,
    })

app = web.Application(debug=True)
app.add_routes([
    web.get('/n/', handle),
    web.get('/n/{name}', handle),
    web.post('/n/{name}', handle),
    web.post('/b/', handle2),
    web.post('/login', do_login),
])


hapic.set_context(AiohttpContext(app))

# print(yaml.dump(
#     json.loads(json.dumps(hapic.generate_doc())),
#     default_flow_style=False,
# ))

web.run_app(app)
