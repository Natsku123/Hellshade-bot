from core.database.models.gw2_guild import Gw2Guild
from core.database.schemas import gw2_guild as schemas
from core.database.crud import CRUDBase, ModelType

from sqlalchemy.orm import Session
from sqlalchemy.future import select
from typing import Optional, List
from uuid import UUID


class CRUDGw2Guild(CRUDBase[Gw2Guild, schemas.CreateGw2Guild, schemas.UpdateGw2Guild]):
    def get_by_server_uuid(self, db: Session, server_uuid: UUID) -> Optional[ModelType]:
        """
        Get Guild by server UUID
        :param db: Database Session
        :param server_uuid: UUID of server
        :return: Object or None
        """

        query = select(self.model).where(self.model.server_uuid == server_uuid)
        result = db.execute(query)
        return result.scalars().first()


gw2_guild: CRUDGw2Guild = CRUDGw2Guild(Gw2Guild)
