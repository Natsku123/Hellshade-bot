from pydantic import BaseModel
from typing import Optional


class PlayerBase(BaseModel):
    discord_id: str
    steam_id: str
    name: str
    hidden: bool

    class Config:
        from_attributes = True


class CreatePlayer(BaseModel):
    discord_id: str
    name: str
    hidden: bool


class UpdatePlayer(BaseModel):
    name: str | None
    hidden: bool | None
    steam_id: str | None
