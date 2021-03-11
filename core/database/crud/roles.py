from core.database.models.roles import Role, RoleEmoji
from core.database.schemas import roles as schemas
from core.database.crud import CRUDBase, ModelType

from sqlalchemy.orm import Session
from sqlalchemy.future import select
from typing import Optional, List
from uuid import UUID


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

    def get_multi_by_server_uuid(
            self, db: Session, server_uuid: UUID
    ) -> List[ModelType]:
        """
        Get roles by server_uuid
        :param db:
        :param server_uuid:
        :return:
        """

        query = select(self.model).where(self.model.server_uuid == server_uuid)
        result = db.execute(query)
        return result.scalars().all()


class CRUDRoleEmoji(
    CRUDBase[RoleEmoji, schemas.CreateRoleEmoji, schemas.UpdateRoleEmoji]
):
    def get_by_role(
            self, db: Session, role_uuid: UUID
    ) -> Optional[ModelType]:
        """
        Get role emoji based on role and server

        :param db: Database Session
        :param role_uuid: UUID of Role
        :return:
        """

        query = select(self.model).where(self.model.role_uuid == role_uuid)
        result = db.execute(query)
        return result.scalars().first()

    def get_by_identifier(
            self, db: Session, identifier: str
    ) -> Optional[ModelType]:
        """
        Get role emoji based on identifier

        :param db: Database Session
        :param identifier: Identifier
        :return:
        """

        query = select(self.model).where(self.model.identifier == identifier)
        result = db.execute(query)
        return result.scalars().first()


role = CRUDRole(Role)
role_emoji = CRUDRoleEmoji(RoleEmoji)
