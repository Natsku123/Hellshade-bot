import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import Column, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship


class Command(Base):
    __tablename__ = "commands"
    uuid = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    server_uuid = Column(GUID(), ForeignKey('servers.uuid'))
    status = Column(Boolean, default=True)
    server = relationship(
        'Server', uselist=False
    )
