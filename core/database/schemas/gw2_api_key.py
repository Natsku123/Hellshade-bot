from uuid import UUID
from pydantic import BaseModel


class Gw2ApiKeyBase(BaseModel):
    player_uuid: UUID
    key: str

    class Config:
        orm_mode = True


class CreateGw2ApiKey(Gw2ApiKeyBase):
    pass


class UpdateGw2ApiKey(BaseModel):
    key: str
