from pydantic import BaseModel
from typing import Optional


class RoleBase(BaseModel):
    discord_id: str
    name: str
    description: str = ""

    class Config:
        orm_mode = True


class CreateRole(RoleBase):
    pass


class UpdateRole(BaseModel):
    name: Optional[str]
    description: Optional[str]
