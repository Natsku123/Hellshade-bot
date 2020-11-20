from core.database.models.members import Member
from core.database.models.levels import Level
from core.database.schemas import members as schemas
from core.database.crud import CRUDBase, ModelType

from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy import desc
from typing import List, Optional


class CRUDMember(CRUDBase[Member, schemas.CreateMember, schemas.UpdateMember]):
    def get_top(
            self, db: Session, server_uuid: UUID, value: int
    ) -> List[ModelType]:
        """
        Get top N on server
        :param db: Database Session
        :param server_uuid: uuid of server
        :param value: number of players to fetch
        :return: List of objects
        """

        query = select(self.model).join(self.model.level).\
            where(self.model.server_uuid == server_uuid).\
            order_by(desc(Level.value), desc(self.model.exp)).\
            limit(value)
        result = db.execute(query)
        return result.all()

    def get_by_ids(
            self, db: Session, player_uuid: UUID, server_uuid
    ) -> Optional[ModelType]:
        """
        Get member by player_uuid and server_uuid
        :param db: Database Session
        :param player_uuid: uuid of player
        :param server_uuid: uuid of server
        :return: Object or None
        """
        query = select(self.model).\
            where(self.model.player_uuid == player_uuid).\
            where(self.model.server_uuid == server_uuid)
        result = db.execute(query)
        return result.scalars().first()


member = CRUDMember(Member)
