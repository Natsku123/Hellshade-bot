from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class RoleBase(BaseModel):
    discord_id: str
    name: str
    description: str = ""
    server_uuid: UUID

    class Config:
        from_attributes = True


class CreateRole(RoleBase):
    pass


class UpdateRole(BaseModel):
    name: str | None
    description: str | None


class RoleEmojiBase(BaseModel):
    identifier: str
    role_uuid: UUID


class CreateRoleEmoji(RoleEmojiBase):
    pass


class UpdateRoleEmoji(BaseModel):
    identifier: str | None
