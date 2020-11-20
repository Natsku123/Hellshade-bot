from core.database.models.levels import Level
from core.database.schemas import levels as schemas
from core.database.crud import CRUDBase, ModelType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional


class CRUDLevel(CRUDBase[Level, schemas.CreateLevel, schemas.UpdateLevel]):
    async def get_by_value(
            self, db: AsyncSession, value: int
    ) -> Optional[ModelType]:
        """
        Get level by value
        :param db: Asynchronous Database Session
        :param value: Level value
        :return: Object or None
        """
        async with self.lock:
            query = select(self.model).where(self.model.value == value)
            result = await db.execute(query)
            return result.scalars().first()


level = CRUDLevel(Level)
