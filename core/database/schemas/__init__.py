from uuid import UUID
from typing import List
from core.database.schemas.members import MemberBase
from core.database.schemas.players import PlayerBase
from core.database.schemas.levels import LevelBase
from core.database.schemas.servers import ServerBase


class Member(MemberBase):
    uuid: UUID
    player: 'Player'
    server: 'Server'
    level: 'Level'


class Player(PlayerBase):
    uuid: UUID
    memberships: List['Member']


class Level(LevelBase):
    uuid: UUID


class Server(ServerBase):
    uuid: UUID
