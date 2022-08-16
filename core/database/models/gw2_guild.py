import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import Column, String, ForeignKey


class Gw2Guild(Base):
    __tablename__ = "gw2_guilds"
    uuid = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    server_uuid = Column(GUID(), ForeignKey('servers.uuid'))
    guild_gw2_id = Column(String, nullable=False)
    guild_owner_uuid = Column(GUID(), ForeignKey('players.uuid'))
    guild_upgrade_channel = Column(String, nullable=True)
