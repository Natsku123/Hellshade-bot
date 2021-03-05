from uuid import UUID
from typing import List
from core.database.schemas.members import MemberBase
from core.database.schemas.players import PlayerBase
from core.database.schemas.levels import LevelBase
from core.database.schemas.servers import ServerBase
from core.database.schemas.roles import RoleBase


class Member(MemberBase):
    uuid: UUID
    player: 'Player'
    server: 'Server'
    level: 'Level'
    roles: List['Role'] = []


class Player(PlayerBase):
    uuid: UUID
    memberships: List['Member'] = []


class Level(LevelBase):
    uuid: UUID


class Server(ServerBase):
    uuid: UUID


class Role(RoleBase):
    uuid: UUID
    members: List['Member'] = []
