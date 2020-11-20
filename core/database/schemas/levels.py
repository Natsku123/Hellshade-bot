from pydantic import BaseModel
from typing import Optional


class LevelBase(BaseModel):
    value: int
    title: Optional[str]
    exp: int

    class Config:
        orm_mode = True


class CreateLevel(LevelBase):
    pass


class UpdateLevel(BaseModel):
    title: Optional[str]
    exp: Optional[int]
