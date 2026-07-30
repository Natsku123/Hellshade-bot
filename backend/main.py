import io
import cairosvg
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
from starlette_graphene3 import GraphQLApp, make_graphiql_handler

from core.database.schemas.graphql import schema
from core.utils.svg import render, render_ip

from config import settings

app = FastAPI(title=settings.SERVER_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/", GraphQLApp(schema, on_get=make_graphiql_handler()))


@app.get('/level-image')
async def level_image(
        name: str = Query("[NAME]"),
        current_exp: int = Query(0),
        needed_exp: int = Query(1000),
        level: int = Query(0),
        icon: str = Query(None)
):
    svg = render(name, current_exp, needed_exp, level, icon)
    bts = cairosvg.svg2png(svg.encode('UTF-8'))
    return StreamingResponse(io.BytesIO(bts), media_type="image/png")

@app.get('/ip')
async def ip(request: Request):
    client_host = request.client.host if request.client is not None else None
    client_ip = request.headers.get(
        "x-real-ip",
        request.headers.get("x-forwarded-for", client_host or "unknown"),
    )
    svg = render_ip(client_ip or "unknown")
    bts = cairosvg.svg2png(svg.encode('UTF-8'))
    return StreamingResponse(io.BytesIO(bts), media_type="image/png")
