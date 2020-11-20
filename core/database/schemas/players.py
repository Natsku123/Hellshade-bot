from pydantic import BaseModel
from typing import Optional


class PlayerBase(BaseModel):
    discord_id: str
    name: str
    hidden: bool

    class Config:
        orm_mode = True


class CreatePlayer(PlayerBase):
    pass


class UpdatePlayer(BaseModel):
    name: Optional[str]
    hidden: Optional[bool]
