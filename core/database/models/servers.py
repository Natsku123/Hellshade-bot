from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.models import Base
from core.database.types import GUID

if TYPE_CHECKING:
    from core.database.models.members import Member


class Server(Base):
    __tablename__ = "servers"

    uuid: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    discord_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    server_exp: Mapped[int] = mapped_column(Integer, nullable=True)
    channel: Mapped[str] = mapped_column(String, nullable=True)
    role_channel: Mapped[str] = mapped_column(String, nullable=True)
    role_message: Mapped[str] = mapped_column(String, nullable=True)
    last_seen: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    members: Mapped[list["Member"]] = relationship("Member", back_populates="server")
