import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from core.database.models.members import member_role_association


class Role(Base):
    __tablename__ = "roles"
    uuid = Column(GUID(), primary_key=True, default=uuid.uuid4)
    discord_id = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    members = relationship(
        'Member', secondary=member_role_association,
        back_populates="roles"
    )


class RoleEmoji(Base):
    __tablename__ = "roleemojis"
    uuid = Column(GUID(), primary_key=True, default=uuid.uuid4())
    identifier = Column(String, nullable=False)
    role_uuid = Column(GUID(), ForeignKey('roles.uuid'), unique=True)
    role = relationship(
        'Role', uselist=False
    )
