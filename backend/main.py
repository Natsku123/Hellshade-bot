from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.graphql import GraphQLApp

from core.database.schemas.graphql import schema

from config import settings

app = FastAPI(title=settings.SERVER_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_route("/", GraphQLApp(schema=schema))
