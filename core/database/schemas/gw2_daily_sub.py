from uuid import UUID
from pydantic import BaseModel

from core.database.models.gw2_daily_sub import DailyType


class Gw2DailySub(BaseModel):
    server_uuid: UUID
    channel_id: str
    message_id: str
    daily_type: DailyType

    class Config:
        orm_mode = True


class CreateGw2DailySub(Gw2DailySub):
    pass


class UpdateGw2DailySub(Gw2DailySub):
    pass
