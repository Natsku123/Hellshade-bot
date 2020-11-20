from core.database.models.levels import Level
from core.database.schemas import levels as schemas
from core.database.crud import CRUDBase, ModelType
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from typing import Optional


class CRUDLevel(CRUDBase[Level, schemas.CreateLevel, schemas.UpdateLevel]):
    def get_by_value(
            self, db: Session, value: int
    ) -> Optional[ModelType]:
        """
        Get level by value
        :param db: Database Session
        :param value: Level value
        :return: Object or None
        """
        query = select(self.model).where(self.model.value == value)
        result = db.execute(query)
        return result.scalars().first()


level = CRUDLevel(Level)
