from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class Gw2GuildUpgradeBase(BaseModel):
    name: str
    server_uuid: UUID
    gw2_guild_uuid: UUID
    message_id: Optional[str] = None
    completed_on: bool = False

    class Config:
        orm_mode = True


class CreateGw2GuildUpgrade(Gw2GuildUpgradeBase):
    pass


class UpdateGw2GuildUpgrade(Gw2GuildUpgradeBase):
    pass
