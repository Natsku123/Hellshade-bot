import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship


class Member(Base):
    __tablename__ = "members"
    uuid = Column(GUID(), primary_key=True, default=uuid.uuid4)
    exp = Column(Integer, nullable=False, default=0)
    player_uuid = Column(GUID(), ForeignKey('players.uuid'))
    server_uuid = Column(GUID(), ForeignKey('servers.uuid'))
    level_uuid = Column(GUID(), ForeignKey('levels.uuid'), nullable=True)
    player = relationship(
        'Player', uselist=False, back_populates='memberships'
    )
    server = relationship('Server', uselist=False, back_populates='members')
    level = relationship('Level', uselist=False)
