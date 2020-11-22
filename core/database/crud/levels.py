from core.database.models.levels import Level
from core.database.schemas import levels as schemas
from core.database.crud import CRUDBase, ModelType
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.future import select
from typing import Optional, List
from core.utils import level_exp


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

    def get_highest(
            self, db: Session
    ) -> Optional[ModelType]:
        """
        Get highest level
        :param db: Database Session
        :return: Object or None
        """
        query = select(self.model).order_by(desc(self.model.value))
        result = db.execute(query)
        return result.scalars().first()

    def generate_many(
            self, db: Session, to: int
    ) -> List[ModelType]:
        """
        Generate many levels
        :param db: Database Session
        :param to: Level value to generate
        :return: List of generated objects
        """
        highest = self.get_highest(db)

        if highest is None:
            start_value = 0
        else:
            start_value = highest.value
        levels = []

        for i in range(start_value + 1, to + 1):
            levels.append(Level(**{
                "value": i,
                "exp": level_exp(i),
                "title": None
            }))
        db.add_all(levels)
        db.flush()
        db.commit()

        for lvl in levels:
            db.refresh(lvl)

        return levels


level = CRUDLevel(Level)
