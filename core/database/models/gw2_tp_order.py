import uuid
import enum
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import Boolean, Integer, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column


class TPOrderType(enum.Enum):
    Buy = enum.auto()
    Sell = enum.auto()


class Gw2TPOrder(Base):
    __tablename__ = "gw2_tp_orders"

    uuid: Mapped[str] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    player_uuid: Mapped[str] = mapped_column(GUID(), ForeignKey('players.uuid'))
    gw2_item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    last_price: Mapped[int] = mapped_column(Integer, nullable=True)
    order_type: Mapped[TPOrderType] = mapped_column(Enum(TPOrderType), nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
