from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class CommandBase(BaseModel):
    name: str
    server_uuid: UUID
    status: bool

    class Config:
        orm_mode = True


class CreateCommand(BaseModel):
    name: str
    server_uuid: UUID
    status: Optional[bool] = True


class UpdateCommand(BaseModel):
    status: bool
