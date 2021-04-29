import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import Column, Text, String, Integer


class Subscription(Base):
    __tablename__ = "steamposts_subscriptions"
    uuid = Column(GUID(), primary_key=True, default=uuid.uuid4)
    channel_id = Column(String, nullable=False)
    app_id = Column(Integer, nullable=False)


class Post(Base):
    __tablename__ = "steamposts"
    uuid = Column(GUID(), primary_key=True, default=uuid.uuid4)
    steam_gid = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
