from asyncio import Lock
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy import delete, update
from core.database.models import Base
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generic, TypeVar, Type, Any, Optional, List, Union, Dict


ModelType = TypeVar("ModelType", bound=Base)
CreateType = TypeVar("CreateType", bound=BaseModel)
UpdateType = TypeVar("UpdateType", bound=BaseModel)

session_lock = Lock()


class CRUDBase(Generic[ModelType, CreateType, UpdateType]):
    """CRUD Base for models and schemas"""

    def __init__(self, model: Type[ModelType]):
        self.model = model
        self.lock = session_lock

    async def get(
            self, db: AsyncSession, uuid: UUID
    ) -> Optional[ModelType]:
        """
        Get an object by uuid
        :param db: Asynchronous Database Session
        :param uuid: uuid of the object
        :return: Object or None
        """
        async with session_lock:
            query = select(self.model).where(self.model.uuid == uuid)

            result = await db.execute(query)
            return result.scalars().first()

    async def get_by_discord(
            self, db: AsyncSession, discord_id: Union[int, str]
    ) -> Optional[ModelType]:
        """
        Get an object by discord_id
        :param db: Asynchronous Database Session
        :param discord_id: Discord ID
        :return: Object or None
        """
        if isinstance(discord_id, int):
            discord_id = str(discord_id)

        async with self.lock:
            query = select(self.model).where(self.model.discord_id == discord_id)
            result = await db.execute(query)
            return result.scalars().first()

    async def get_multi(
            self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple objects
        :param db: Asynchronous Database Session
        :param skip: Skip N objects
        :param limit: Return only N objects
        :return: List of objects
        """
        async with self.lock:
            query = select(self.model).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()

    async def create(
            self, db: AsyncSession, *, obj_in: CreateType
    ) -> ModelType:
        """
        Create a new object
        :param db: Asynchronous Database Session
        :param obj_in: Pydantic type of the object to create
        :return: Object
        """
        async with self.lock:
            db_obj = self.model(**obj_in.dict())

            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)

            return db_obj

    async def update(
            self, db: AsyncSession, *, db_obj: ModelType,
            obj_in: Union[UpdateType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update data of an object
        :param db: Asynchronous Database Session
        :param db_obj: Object to be updated
        :param obj_in: Update data
        :return: Object
        """

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        async with self.lock:
            query = update(self.model).where(self.model.uuid == db_obj.uuid). \
                values(**update_data)

            await db.execute(query)
            await db.commit()

            await db.refresh(db_obj)

            return db_obj

    async def remove(
            self, db: AsyncSession, *, uuid: UUID
    ) -> ModelType:
        """
        Delete object
        :param db: Asynchronous Database Session
        :param uuid: uuid of object
        :return: Object
        """
        async with self.lock:
            query = select(self.model).where(self.model.uuid == uuid)
            result = await db.execute(query)
            obj = await result.first()

            if obj is not None:
                del_query = delete(self.model).where(self.model.uuid == uuid)
                await db.execute(del_query)
                await db.commit()

            return obj
