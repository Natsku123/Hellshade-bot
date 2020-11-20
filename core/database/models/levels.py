import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import Column, String, Integer


class Level(Base):
    __tablename__ = "levels"
    uuid = Column(GUID(), primary_key=True, default=uuid.uuid4)
    value = Column(Integer, nullable=False)
    title = Column(String, nullable=True, unique=True)
    exp = Column(Integer, nullable=False, default=0)

