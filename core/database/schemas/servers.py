from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ServerBase(BaseModel):
    discord_id: str
    name: str
    server_exp: int
    channel: Optional[str]
    role_channel: Optional[str]
    role_message: Optional[str]
    last_seen: Optional[datetime]

    class Config:
        orm_mode = True


class CreateServer(ServerBase):
    pass


class UpdateServer(BaseModel):
    name: Optional[str]
    server_exp: Optional[int]
    channel: Optional[str]
    role_channel: Optional[str]
    role_message: Optional[str]
    last_seen: Optional[datetime]
