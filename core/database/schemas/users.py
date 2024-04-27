from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class UserBase(BaseModel):
    username: str

    class Config:
        from_attributes = True


class CreateUser(UserBase):
    password: str


class UpdateUser(BaseModel):
    username: str | None
    password: str | None


class User(UserBase):
    uuid: UUID
