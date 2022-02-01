from core.database.models.commands import Command
from core.database.schemas import commands as schemas
from core.database.crud import CRUDBase, ModelType

from sqlalchemy.orm import Session
from sqlalchemy.future import select
from typing import Optional
from uuid import UUID


class CRUDCommand(CRUDBase[Command, schemas.CreateCommand, schemas.UpdateCommand]):
    def get_by_server_and_name(self, db: Session, server_uuid: UUID, name: str) -> Optional[ModelType]:
        """
        Get command by server uuid and command name
        :param db: Database Session
        :param server_uuid: Server UUID
        :param name: Name of Command
        :return: Object or None
        """

        query = select(self.model).where(self.model.name == name).where(self.model.server_uuid == server_uuid)
        result = db.execute(query)
        return result.scalars().first()

    def get_enabled_by_name(self, db: Session, name: str) -> Optional[ModelType]:
        """
        Get enabled commands by command name
        :param db: Database Session
        :param name: Name of Command
        :return: Object or None
        """

        query = select(self.model).where(self.model.name == name).where(self.model.status is True)
        result = db.execute(query)
        return result.scalars().all()


command: CRUDCommand = CRUDCommand(Command)
