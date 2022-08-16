from core.database.models.gw2_api_key import Gw2ApiKey
from core.database.schemas import gw2_api_key as schemas
from core.database.crud import CRUDBase, ModelType

from sqlalchemy.orm import Session
from sqlalchemy.future import select
from typing import Optional, List
from uuid import UUID


class CRUDGw2ApiKey(CRUDBase[Gw2ApiKey, schemas.CreateGw2ApiKey, schemas.UpdateGw2ApiKey]):
    def get_by_player_uuid(self, db: Session, player_uuid: UUID) -> Optional[ModelType]:
        """
        Get ApiKey by player UUID
        :param db: Database Session
        :param player_uuid: UUID of player
        :return: Object or None
        """

        query = select(self.model).where(self.model.player_uuid == player_uuid)
        result = db.execute(query)
        return result.scalars().first()


gw2_api_key: CRUDGw2ApiKey = CRUDGw2ApiKey(Gw2ApiKey)
