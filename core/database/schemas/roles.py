from pydantic import BaseModel


class RoleBase(BaseModel):
    discord_id: str
    name: str

    class Config:
        orm_mode = True


class CreateRole(RoleBase):
    pass


class UpdateRole(BaseModel):
    name: str
