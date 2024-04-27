from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database.models.dota_guild import DotaGuild
from core.database.schemas import dota_guild as schemas
from core.database.crud import CRUDBase, ModelType


class CRUDDotaGuild(CRUDBase[DotaGuild, schemas.CreateDotaGuild, schemas.UpdateDotaGuild]):
    def get_multi_by_server_uuid(
            self, db: Session, server_uuid: UUID
    ) -> list[ModelType]:
        """
        Get Dota Guilds by server_uuid
        :param db:
        :param server_uuid:
        :return:
        """

        query = select(self.model).where(self.model.server_uuid == server_uuid)
        result = db.execute(query)
        return result.scalars().all()

    def get_by_guild_id_server_uuid(self, db: Session, guild_id: int, server_uuid: UUID) -> ModelType | None:
        query = select(self.model).where(self.model.guild_id == guild_id).where(self.model.server_uuid == server_uuid)
        result = db.execute(query)
        return result.scalars().first()


dota_guild = CRUDDotaGuild(DotaGuild)
