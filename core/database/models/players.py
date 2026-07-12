import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database.models.members import Member


class Player(Base):
    __tablename__ = "players"

    uuid: Mapped[str] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    discord_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    steam_id: Mapped[str] = mapped_column(String, nullable=True, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    memberships: Mapped[list[Member]] = relationship('Member', back_populates='player')

    def __repr__(self):
        return f"Player({self.uuid=}, {self.discord_id=}, {self.name=}, " \
               f"{self.hidden=})"
