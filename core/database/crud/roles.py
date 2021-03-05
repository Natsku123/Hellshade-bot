from core.database.models.roles import Role
from core.database.schemas import roles as schemas
from core.database.crud import CRUDBase, ModelType

from sqlalchemy.orm import Session
from sqlalchemy.future import select
from typing import Optional


class CRUDRole(CRUDBase[Role, schemas.CreateRole, schemas.UpdateRole]):
    def get_by_name(self, db: Session, name: str) -> Optional[ModelType]:
        """
        Get role by name
        :param db: Database Session
        :param name: Name of Role
        :return: Object or None
        """

        query = select(self.model).where(self.model.name == name)
        result = db.execute(query)
        return result.scalars().first()


role = CRUDRole(Role)
