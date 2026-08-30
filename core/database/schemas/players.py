from pydantic import BaseModel, ConfigDict


class PlayerBase(BaseModel):
    discord_id: str
    steam_id: str
    name: str
    hidden: bool

    model_config = ConfigDict(from_attributes=True)


class CreatePlayer(BaseModel):
    discord_id: str
    name: str
    hidden: bool


class UpdatePlayer(BaseModel):
    name: str | None = None
    hidden: bool | None = None
    steam_id: str | None = None
