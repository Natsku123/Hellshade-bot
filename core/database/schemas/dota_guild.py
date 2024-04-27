from uuid import UUID

from pydantic import BaseModel


class DotaGuildBase(BaseModel):
    role_discord_id: str
    name: str
    server_uuid: UUID
    guild_id: int

    class Config:
        from_attributes = True


class CreateDotaGuild(DotaGuildBase):
    pass


class UpdateDotaGuild(BaseModel):
    role_discord_id: str | None
    name: str | None
    server_uuid: UUID | None
    guild_id: int | None
