import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import Integer, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database.models.players import Player
from core.database.models.servers import Server
from core.database.models.levels import Level
from core.database.models.roles import Role


member_role_association = Table(
    'member_role_association', Base.metadata,
    Column('role_uuid', GUID(), ForeignKey('roles.uuid')),
    Column('member_uuid', GUID(), ForeignKey('members.uuid'))
)


class Member(Base):
    __tablename__ = "members"

    uuid: Mapped[str] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    exp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    player_uuid: Mapped[str] = mapped_column(GUID(), ForeignKey('players.uuid'))
    server_uuid: Mapped[str] = mapped_column(GUID(), ForeignKey('servers.uuid'))
    level_uuid: Mapped[str] = mapped_column(GUID(), ForeignKey('levels.uuid'), nullable=True)

    player: Mapped[Player] = relationship(
        'Player', uselist=False, back_populates='memberships'
    )
    server: Mapped[Server] = relationship('Server', uselist=False, back_populates='members')
    level: Mapped[Level] = relationship('Level', uselist=False)
    roles: Mapped[list[Role]] = relationship(
        'Role', secondary=member_role_association,
        back_populates="members"
    )

