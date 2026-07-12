import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database.models.members import Member, member_role_association
from core.database.models.servers import Server


class Role(Base):
    __tablename__ = "roles"

    uuid: Mapped[str] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    discord_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    server_uuid: Mapped[str] = mapped_column(GUID(), ForeignKey('servers.uuid'))

    server: Mapped[Server] = relationship(
        'Server', uselist=False
    )
    members: Mapped[list[Member]] = relationship(
        'Member', secondary=member_role_association,
        back_populates="roles"
    )


class RoleEmoji(Base):
    __tablename__ = "roleemojis"

    uuid: Mapped[str] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    identifier: Mapped[str] = mapped_column(String, nullable=False)
    role_uuid: Mapped[str] = mapped_column(GUID(), ForeignKey('roles.uuid'), unique=True)

    role: Mapped[Role] = relationship(
        'Role', uselist=False
    )
