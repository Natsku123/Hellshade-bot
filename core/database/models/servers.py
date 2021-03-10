import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship


class Server(Base):
    __tablename__ = "servers"
    uuid = Column(GUID(), primary_key=True, default=uuid.uuid4)
    discord_id = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    server_exp = Column(Integer, nullable=True)
    channel = Column(String, nullable=True)
    role_channel = Column(String, nullable=True)
    role_message = Column(String, nullable=True)
    members = relationship('Member')
