from uuid import UUID
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy import delete, update
from sqlalchemy.orm import Session
from core.database.models import Base
from typing import Generic, TypeVar, Type, Any, Optional, List, Union, Dict


ModelType = TypeVar("ModelType", bound=Base)
CreateType = TypeVar("CreateType", bound=BaseModel)
UpdateType = TypeVar("UpdateType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateType, UpdateType]):
    """CRUD Base for models and schemas"""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get_count(
            self, db: Session
    ) -> int:
        """
        Get number of objects
        :param db: Database Session
        :return:
        """
        query = select(self.model)
        result = db.execute(query)
        return result.count()

    def get(
            self, db: Session, uuid: UUID
    ) -> Optional[ModelType]:
        """
        Get an object by uuid
        :param db: Database Session
        :param uuid: uuid of the object
        :return: Object or None
        """
        query = select(self.model).where(self.model.uuid == uuid)

        result = db.execute(query)
        return result.scalars().first()

    def get_by_discord(
            self, db: Session, discord_id: Union[int, str]
    ) -> Optional[ModelType]:
        """
        Get an object by discord_id
        :param db: Database Session
        :param discord_id: Discord ID
        :return: Object or None
        """
        if isinstance(discord_id, int):
            discord_id = str(discord_id)

        query = select(self.model).where(self.model.discord_id == discord_id)
        result = db.execute(query)
        return result.scalars().first()

    def get_multi(
            self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple objects
        :param db: Database Session
        :param skip: Skip N objects
        :param limit: Return only N objects
        :return: List of objects
        """
        query = select(self.model).offset(skip).limit(limit)
        result = db.execute(query)
        return result.scalars().all()

    def create(
            self, db: Session, *, obj_in: CreateType
    ) -> ModelType:
        """
        Create a new object
        :param db: Database Session
        :param obj_in: Pydantic type of the object to create
        :return: Object
        """
        db_obj = self.model(**obj_in.dict())

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return db_obj

    def update(
            self, db: Session, *, db_obj: ModelType,
            obj_in: Union[UpdateType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update data of an object
        :param db: Database Session
        :param db_obj: Object to be updated
        :param obj_in: Update data
        :return: Object
        """

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        query = update(self.model).where(self.model.uuid == db_obj.uuid). \
            values(**update_data)

        db.execute(query)
        db.commit()

        db.refresh(db_obj)

        return db_obj

    def remove(
            self, db: Session, *, uuid: UUID
    ) -> ModelType:
        """
        Delete object
        :param db: Database Session
        :param uuid: uuid of object
        :return: Object
        """
        query = select(self.model).where(self.model.uuid == uuid)
        result = db.execute(query)
        obj = result.scalars().first()

        if obj is not None:
            del_query = delete(self.model).where(self.model.uuid == uuid)
            db.execute(del_query)
            db.commit()

        return obj
