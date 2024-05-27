from pydantic import BaseModel
from typing import Optional


class LevelBase(BaseModel):
    value: int
    title: str | None = None
    exp: int

    class Config:
        from_attributes = True


class CreateLevel(LevelBase):
    pass


class UpdateLevel(BaseModel):
    title: str | None = None
    exp: int | None = None
