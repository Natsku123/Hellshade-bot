from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class MemberBase(BaseModel):
    exp: int
    player_uuid: UUID
    server_uuid: UUID
    level_uuid: UUID | None

    class Config:
        from_attributes = True


class CreateMember(MemberBase):
    pass


class UpdateMember(BaseModel):
    exp: int | None
    level_uuid: UUID | None
