from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class MemberBase(BaseModel):
    exp: int
    player_uuid: UUID
    server_uuid: UUID
    level_uuid: Optional[UUID]

    class Config:
        orm_mode = True


class CreateMember(MemberBase):
    pass


class UpdateMember(BaseModel):
    exp: Optional[int]
    level_uuid: Optional[UUID]
