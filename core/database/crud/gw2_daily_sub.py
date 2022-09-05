from core.database.models.gw2_daily_sub import Gw2DailySub, DailyType
from core.database.schemas import gw2_daily_sub as schemas
from core.database.crud import CRUDBase, ModelType

from sqlalchemy import and_
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from typing import Optional, List
from uuid import UUID


class CRUDGw2DailySub(CRUDBase[Gw2DailySub, schemas.CreateGw2DailySub, schemas.UpdateGw2DailySub]):
    def get_by_server_uuid(self, db: Session, server_uuid: UUID) -> List[ModelType]:
        """
        Get Daily subscriptions by server UUID
        :param db: Database Session
        :param server_uuid: UUID of server
        :return: Object or None
        """

        query = select(self.model).where(self.model.server_uuid == server_uuid)
        result = db.execute(query)
        return result.scalars().all()

    def get_by_category(self, db: Session, server_uuid: UUID, category: DailyType) -> Optional[ModelType]:
        """
        Get Daily subscriptions by server UUID and category
        :param db: Database Session
        :param server_uuid: UUID of server
        :param category: Category
        :return: Object or None
        """

        query = select(self.model).where(and_(self.model.server_uuid == server_uuid, self.model.daily_type == category))
        result = db.execute(query)
        return result.scalars().first()


gw2_daily_sub: CRUDGw2DailySub = CRUDGw2DailySub(Gw2DailySub)
