from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class UserBase(BaseModel):
    username: str

    class Config:
        orm_mode = True


class CreateUser(UserBase):
    password: str


class UpdateUser(BaseModel):
    username: Optional[str]
    password: Optional[str]


class User(UserBase):
    uuid: UUID
