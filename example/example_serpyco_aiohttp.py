# coding: utf-8
from dataclasses import dataclass
import json

from aiohttp import web

from hapic import Hapic
from hapic import HapicData
from hapic.error.serpyco import SerpycoDefaultErrorBuilder
from hapic.ext.aiohttp.context import AiohttpContext
from hapic.processor.serpyco import SerpycoProcessor

hapic = Hapic(async_=True)
hapic.set_processor_class(SerpycoProcessor)


@dataclass
class UserDocument(object):
    id: str
    name: str
    password: str


@dataclass
class UserModel(object):
    id: str
    name: str


@dataclass
class GetUserPath(object):
    id: str


@hapic.with_api_doc()
@hapic.input_path(GetUserPath)
@hapic.output_body(UserModel)
async def get_user(request, hapic_data: HapicData):
    return UserModel(id=hapic_data.path.id, name="Bob")


app = web.Application()
app.add_routes([web.get(r"/user/{id}", get_user)])

context = AiohttpContext(app, default_error_builder=SerpycoDefaultErrorBuilder())
hapic.set_context(context)
hapic.add_documentation_view("/api/doc")
print(json.dumps(hapic.generate_doc()))
web.run_app(app)
