from uuid import UUID
from pydantic import BaseModel, ConfigDict


class CommandBase(BaseModel):
    name: str
    server_uuid: UUID
    status: bool

    model_config = ConfigDict(from_attributes=True)


class CreateCommand(BaseModel):
    name: str
    server_uuid: UUID
    status: bool | None = True


class UpdateCommand(BaseModel):
    status: bool
