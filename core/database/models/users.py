import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import Column, String


class User(Base):
    __tablename__ = "users"
    uuid = Column(GUID(), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
