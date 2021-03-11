from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class RoleBase(BaseModel):
    discord_id: str
    name: str
    description: str = ""
    server_uuid: UUID

    class Config:
        orm_mode = True


class CreateRole(RoleBase):
    pass


class UpdateRole(BaseModel):
    name: Optional[str]
    description: Optional[str]


class RoleEmojiBase(BaseModel):
    identifier: str
    role_uuid: UUID


class CreateRoleEmoji(RoleEmojiBase):
    pass


class UpdateRoleEmoji(BaseModel):
    identifier: Optional[str]
