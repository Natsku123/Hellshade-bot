from core.database import Base
from core.database.models.members import Member
from core.database.models.levels import Level
from core.database.models.players import Player
from core.database.models.servers import Server
from core.database.models.users import User

from core.database.types import GUID
from sqlalchemy import Column, ForeignKey, Table

member_role_association = Table(
    'member_role_association', Base.metadata,
    Column('role_uuid', GUID(), ForeignKey('roles.uuid')),
    Column('member_uuid', GUID(), ForeignKey('members.uuid'))
)