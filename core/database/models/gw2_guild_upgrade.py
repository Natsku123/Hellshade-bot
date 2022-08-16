import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import Column, String, ForeignKey, Boolean


class Gw2GuildUpgrade(Base):
    __tablename__ = "gw2_guild_upgrades"
    uuid = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    gw2_guild_uuid = Column(GUID(), ForeignKey('gw2_guilds.uuid'))
    message_id = Column(String)
    completed = Column(Boolean, default=False)
