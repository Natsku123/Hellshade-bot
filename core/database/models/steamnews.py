import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import Text, String, Integer
from sqlalchemy.orm import Mapped, mapped_column


class Subscription(Base):
    __tablename__ = "steamposts_subscriptions"

    uuid: Mapped[str] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    channel_id: Mapped[str] = mapped_column(String, nullable=False)
    app_id: Mapped[int] = mapped_column(Integer, nullable=False)


class Post(Base):
    __tablename__ = "steamposts"

    uuid: Mapped[str] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    steam_gid: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
