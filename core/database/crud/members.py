from core.database.models.members import Member
from core.database.models.levels import Level
from core.database.schemas import members as schemas
from core.database.crud import CRUDBase, ModelType

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from typing import List, Optional


class CRUDMember(CRUDBase[Member, schemas.CreateMember, schemas.UpdateMember]):
    async def get_top(
            self, db: AsyncSession, server_uuid: UUID, value: int
    ) -> List[ModelType]:
        """
        Get top N on server
        :param db: Asynchronous Database Session
        :param server_uuid: uuid of server
        :param value: number of players to fetch
        :return: List of objects
        """

        async with self.lock:
            query = select(self.model).join(self.model.level).\
                where(self.model.server_uuid == server_uuid).\
                order_by(desc(Level.value), desc(self.model.exp)).\
                limit(value)
            result = await db.execute(query)
            return result.all()

    async def get_by_ids(
            self, db: AsyncSession, player_uuid: UUID, server_uuid
    ) -> Optional[ModelType]:
        """
        Get member by player_uuid and server_uuid
        :param db: Asynchronous Database Session
        :param player_uuid: uuid of player
        :param server_uuid: uuid of server
        :return: Object or None
        """
        async with self.lock:
            query = select(self.model).\
                where(self.model.player_uuid == player_uuid).\
                where(self.model.server_uuid == server_uuid)
            result = await db.execute(query)
            return result.scalars().first()


member = CRUDMember(Member)
