import uuid
import enum
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import Column, Boolean, Integer, ForeignKey, Enum


class TPOrderType(enum.Enum):
    Buy = enum.auto()
    Sell = enum.auto()


class Gw2TPOrder(Base):
    __tablename__ = "gw2_tp_orders"
    uuid = Column(GUID(), primary_key=True, default=uuid.uuid4)
    player_uuid = Column(GUID(), ForeignKey('players.uuid'))
    gw2_item_id = Column(Integer, nullable=False)
    last_price = Column(Integer, nullable=True)
    order_type = Column(Enum(TPOrderType), nullable=False)
    done = Column(Boolean, default=False)
