from uuid import UUID
from typing import List
from core.database.schemas.members import MemberBase
from core.database.schemas.players import PlayerBase
from core.database.schemas.levels import LevelBase
from core.database.schemas.servers import ServerBase
from core.database.schemas.roles import RoleBase, RoleEmojiBase


class Member(MemberBase):
    uuid: UUID
    player: 'Player'
    server: 'Server'
    level: 'Level'
    roles: list['Role'] = []


class Player(PlayerBase):
    uuid: UUID
    memberships: list['Member'] = []


class Level(LevelBase):
    uuid: UUID


class Server(ServerBase):
    uuid: UUID


class Role(RoleBase):
    uuid: UUID
    server: 'Server'
    members: list['Member'] = []


class RoleEmoji(RoleEmojiBase):
    uuid: UUID
    role: 'Role'
