import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship


class Player(Base):
    __tablename__ = "players"
    uuid = Column(GUID(), primary_key=True, default=uuid.uuid4)
    discord_id = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    hidden = Column(Boolean, nullable=False, default=True)
    memberships = relationship('Member')

    def __repr__(self):
        return f"Player({self.uuid=}, {self.discord_id=}, {self.name=}, " \
               f"{self.hidden=})"
