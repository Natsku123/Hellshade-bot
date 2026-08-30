from pydantic import BaseModel, ConfigDict


class SubscriptionBase(BaseModel):
    channel_id: str
    app_id: int

    model_config = ConfigDict(from_attributes=True)


class PostBase(BaseModel):
    steam_gid: str
    title: str
    content: str

    model_config = ConfigDict(from_attributes=True)


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
