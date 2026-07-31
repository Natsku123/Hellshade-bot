from pydantic import BaseModel, ConfigDict


class LevelBase(BaseModel):
    value: int
    title: str | None = None
    exp: int

    model_config = ConfigDict(from_attributes=True)


class CreateLevel(LevelBase):
    pass


class UpdateLevel(BaseModel):
    title: str | None = None
    exp: int | None = None
