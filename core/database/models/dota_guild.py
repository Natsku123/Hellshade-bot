import uuid
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.models import Base
from core.database.models.servers import Server
from core.database.types import GUID


class DotaGuild(Base):
    __tablename__ = "dota_guilds"

    uuid: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    role_discord_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    server_uuid: Mapped[UUID] = mapped_column(GUID(), ForeignKey('servers.uuid'))
    guild_id: Mapped[int] = mapped_column(Integer, nullable=False)

    server: Mapped[Server] = relationship(
        'Server', uselist=False
    )
