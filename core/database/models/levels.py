import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column


class Level(Base):
    __tablename__ = "levels"

    uuid: Mapped[str] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=True, unique=True)
    exp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

