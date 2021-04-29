from pydantic import BaseModel
from typing import Optional


class SubscriptionBase(BaseModel):
    channel_id: str
    app_id: int

    class Config:
        orm_mode = True


class PostBase(BaseModel):
    steam_gid: str
    title: str
    content: str

    class Config:
        orm_mode = True


class CreateSubscription(SubscriptionBase):
    pass


class CreatePost(PostBase):
    pass


class UpdateSubscription(BaseModel):
    channel_id: Optional[str]
    app_id: Optional[int]


class UpdatePost(BaseModel):
    title: Optional[str]
    content: Optional[str]
