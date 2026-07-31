from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ServerBase(BaseModel):
    discord_id: str
    name: str
    server_exp: int | None = None
    channel: str | None = None
    role_channel: str | None = None
    role_message: str | None = None
    last_seen: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CreateServer(ServerBase):
    pass


class UpdateServer(BaseModel):
    name: str | None = None
    server_exp: int | None = None
    channel: str | None = None
    role_channel: str | None = None
    role_message: str | None = None
    last_seen: datetime | None = None
