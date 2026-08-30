from uuid import UUID
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    username: str

    model_config = ConfigDict(from_attributes=True)


class CreateUser(UserBase):
    password: str


class UpdateUser(BaseModel):
    username: str | None
    password: str | None


class User(UserBase):
    uuid: UUID
