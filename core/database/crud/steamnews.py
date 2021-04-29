from core.database.models.steamnews import Subscription, Post
from core.database.schemas import steamnews as schemas
from core.database.crud import CRUDBase, ModelType
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from typing import Optional, Union, List


class CRUDPost(CRUDBase[Post, schemas.CreatePost, schemas.UpdatePost]):
    def get_by_gid(self, db: Session, gid: str) -> Optional[ModelType]:
        """
        Get Post by Steam News GID.
        :param db: Database Session
        :param gid: Steam News GID
        :return: Object or None
        """
        query = select(self.model).where(self.model.steam_gid == gid)
        result = db.execute(query)
        return result.scalars().first()


class CRUDSubscription(CRUDBase[Subscription, schemas.CreateSubscription, schemas.UpdateSubscription]):
    def get_multi_by_channel_id(
            self, db: Session, channel_id: Union[str, int]
    ) -> List[ModelType]:
        """
        Get Subscriptions by channel id
        :param db:
        :param channel_id:
        :return:
        """
        if isinstance(channel_id, int):
            channel_id = str(channel_id)
        query = select(self.model).where(self.model.channel_id == channel_id)
        result = db.execute(query)
        return result.scalars().all()


post = CRUDPost(Post)
subscription = CRUDSubscription(Subscription)
