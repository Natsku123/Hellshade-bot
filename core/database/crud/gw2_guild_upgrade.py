from core.database.models.gw2_guild_upgrade import Gw2GuildUpgrade
from core.database.schemas import gw2_guild_upgrade as schemas
from core.database.crud import CRUDBase, ModelType

from sqlalchemy.orm import Session
from sqlalchemy.future import select
from typing import Optional, List
from uuid import UUID


class CRUDGw2GuildUpgrade(CRUDBase[Gw2GuildUpgrade, schemas.CreateGw2GuildUpgrade, schemas.UpdateGw2GuildUpgrade]):
    def get_by_guild_uuid(self, db: Session, guild_uuid: UUID) -> Optional[ModelType]:
        """
        Get Upgrade by guild UUID
        :param db: Database Session
        :param guild_uuid: UUID of guild
        :return: Object or None
        """

        query = select(self.model).where(self.model.gw2_guild_uuid == guild_uuid)
        result = db.execute(query)
        return result.scalars().first()


gw2_guild_upgrade: CRUDGw2GuildUpgrade = CRUDGw2GuildUpgrade(Gw2GuildUpgrade)
