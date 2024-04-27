from pydantic import BaseModel
from typing import Optional


class SubscriptionBase(BaseModel):
    channel_id: str
    app_id: int

    class Config:
        from_attributes = True


class PostBase(BaseModel):
    steam_gid: str
    title: str
    content: str

    class Config:
        from_attributes = True


class CreateSubscription(SubscriptionBase):
    pass


class CreatePost(PostBase):
    pass


class UpdateSubscription(BaseModel):
    channel_id: str | None
    app_id: int | None


class UpdatePost(BaseModel):
    title: str | None
    content: str | None
