import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import Column, String, ForeignKey


class Gw2ApiKey(Base):
    __tablename__ = "gw2_api_keys"
    uuid = Column(GUID(), primary_key=True, default=uuid.uuid4)
    player_uuid = Column(GUID(), ForeignKey('players.uuid'), nullable=False)
    key = Column(String, nullable=False)
