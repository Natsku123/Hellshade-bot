from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class Gw2GuildBase(BaseModel):
    name: str
    server_uuid: UUID
    guild_gw2_id: str
    guild_owner_uuid: Optional[UUID] = None
    guild_upgrade_channel: Optional[str] = None

    class Config:
        orm_mode = True


class CreateGw2Guild(Gw2GuildBase):
    pass


class UpdateGw2Guild(Gw2GuildBase):
    pass
