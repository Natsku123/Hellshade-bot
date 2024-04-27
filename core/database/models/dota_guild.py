import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship


class DotaGuild(Base):
    __tablename__ = "dota_guilds"
    uuid = Column(GUID(), primary_key=True, default=uuid.uuid4)
    role_discord_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    server_uuid = Column(GUID(), ForeignKey('servers.uuid'))
    guild_id = Column(Integer, nullable=False)
    server = relationship(
        'Server', uselist=False
    )
