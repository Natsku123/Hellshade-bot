import uuid
import enum
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import Column, String, ForeignKey, Enum


class DailyType(enum.Enum):
    PvE = enum.auto()
    PvP = enum.auto()
    WvW = enum.auto()
    Fractals = enum.auto()
    Strikes = enum.auto()
    LivingWorld = enum.auto()


class Gw2DailySub(Base):
    __tablename__ = "gw2_daily_subs"
    uuid = Column(GUID(), primary_key=True, default=uuid.uuid4)
    server_uuid = Column(GUID(), ForeignKey('servers.uuid'), nullable=False)
    channel_id = Column(String, nullable=False)
    message_id = Column(String, nullable=False)
    daily_type = Column(Enum(DailyType), nullable=False)
