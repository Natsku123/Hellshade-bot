import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database.models.servers import Server


class DotaGuild(Base):
    __tablename__ = "dota_guilds"

    uuid: Mapped[str] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    role_discord_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    server_uuid: Mapped[str] = mapped_column(GUID(), ForeignKey('servers.uuid'))
    guild_id: Mapped[int] = mapped_column(Integer, nullable=False)

    server: Mapped[Server] = relationship(
        'Server', uselist=False
    )
