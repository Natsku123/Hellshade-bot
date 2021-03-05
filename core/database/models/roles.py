import uuid
from core.database.models import Base, member_role_association
from core.database.types import GUID
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship


class Role(Base):
    __tablename__ = "roles"
    uuid = Column(GUID(), primary_key=True, default=uuid.uuid4)
    discord_id = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    members = relationship(
        'Member', secondary=member_role_association,
        back_populates="roles"
    )
