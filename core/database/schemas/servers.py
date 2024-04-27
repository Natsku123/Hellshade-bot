from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ServerBase(BaseModel):
    discord_id: str
    name: str
    server_exp: int
    channel: str | None = None
    role_channel: str | None = None
    role_message: str | None = None
    last_seen: datetime | None = None

    class Config:
        from_attributes = True


class CreateServer(ServerBase):
    pass


class UpdateServer(BaseModel):
    name: str | None
    server_exp: int | None
    channel: str | None
    role_channel: str | None
    role_message: str | None
    last_seen: datetime | None
