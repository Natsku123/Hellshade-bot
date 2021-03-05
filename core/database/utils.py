from uuid import UUID
from discord.ext.commands import Context
from sqlalchemy.orm import Session
from typing import Optional, Union

from core.database.crud.servers import CRUDServer
from core.database.crud.servers import server as crud_server
from core.database.crud.players import CRUDPlayer
from core.database.crud.players import player as crud_player
from core.database.crud.members import CRUDMember
from core.database.crud.members import member as crud_member
from core.database.crud.levels import CRUDLevel
from core.database.crud.levels import level as crud_level
from core.database.crud.roles import role as crud_role
from core.database.schemas.servers import CreateServer
from core.database.schemas.players import CreatePlayer
from core.database.schemas.members import CreateMember
from core.database.schemas.levels import CreateLevel

from core.utils import level_exp


def get_create(
        db: Session, crud, *, obj_in=Union[
            CreateServer, CreatePlayer, CreateMember, CreateLevel
        ]
):
    """
    Create object if it doesn't exist
    :param db: Database session
    :param crud: Crud-object to be used
    :param obj_in: creation object
    :return: Object
    """

    # Get/Create Level
    if isinstance(crud, CRUDLevel) and isinstance(obj_in, CreateLevel):

        obj = crud.get_by_value(db, obj_in.value)

        if obj is None:
            obj = crud_level.generate_many(db, obj_in.value)[-1]

    # Get/Create Server
    elif isinstance(crud, CRUDServer) and isinstance(obj_in, CreateServer):
        obj = crud.get_by_discord(
            db, obj_in.discord_id
        )

        if obj is None:
            obj = crud_server.create(
                db, obj_in=obj_in
            )

    # Get/Create Player
    elif isinstance(crud, CRUDPlayer) and isinstance(obj_in, CreatePlayer):
        obj = crud.get_by_discord(
            db, obj_in.discord_id
        )

        if obj is None:
            obj = crud_player.create(
                db, obj_in=obj_in
            )

    # Get/Create Member
    elif isinstance(crud, CRUDMember) and isinstance(obj_in, CreateMember):
        obj = crud_member.get_by_ids(
            db, obj_in.player_uuid, obj_in.server_uuid
        )
        if obj is None:
            obj = crud_member.create(
                db, obj_in=obj_in
            )
    else:
        raise NotImplemented

    return obj


def get_create_ctx(
        ctx: Context, db: Session, crud, overrides: Optional[dict]={}
):
    """
    Create object if it doesn't exist with context
    :param ctx: Discord Context
    :param db: Database session
    :param crud: Crud-object to be used
    :param overrides: Override data
    :return: object
    """

    obj = None
    player_uuid = None
    server_uuid = None

    if isinstance(crud, CRUDLevel):
        if overrides.get('level', 1) < 1:
            raise ValueError('Level must be 1 or greater!')

        obj = crud.get_by_value(db, overrides.get('level', 1))

        previous = None

        if overrides.get('level', 1) > 1:
            prev_overrides = overrides
            prev_overrides['levels'] -= 1
            previous = get_create_ctx(ctx, db, crud, prev_overrides)

        if obj is None and \
                (previous is not None or overrides.get('level', 1) == 1):
            level_dict = {
                'title': overrides.get('title'),
                'exp': level_exp(overrides.get('level', 1)),
                'value': overrides.get('level', 1)
            }
            obj = crud_level.create(db, obj_in=CreateLevel(**level_dict))

    if isinstance(crud, CRUDServer) or isinstance(crud, CRUDMember):
        obj = crud.get_by_discord(
            db, ctx.guild.id
        )

        if obj is None:
            server_dict = {
                "discord_id": ctx.guild.id,
                "name": ctx.guild.name,
                "server_exp": overrides.get('exp', 0),
                "channel": overrides.get('channel_id')
            }
            obj = crud_server.create(
                db, obj_in=CreateServer(**server_dict)
            )

        server_uuid = obj.uuid

    if isinstance(crud, CRUDPlayer) or isinstance(crud, CRUDMember):
        obj = crud.get_by_discord(
            db, ctx.message.author.id
        )

        if obj is None:
            player_dict = {
                "discord_id": ctx.message.author.id,
                "name": ctx.message.author.name,
                "hidden": overrides.get('hidden', False)
            }
            obj = crud_player.create(
                db, obj_in=CreatePlayer(**player_dict)
            )

        player_uuid = obj.uuid

    if isinstance(crud, CRUDMember):
        obj = crud_member.get_by_ids(
            db, player_uuid, server_uuid
        )
        if obj is None:
            member_dict = {
                "exp": overrides.get('exp', 0),
                "player_uuid": player_uuid,
                "server_uuid": server_uuid,
                "level_uuid": None,

            }
            obj = crud_member.create(
                db, obj_in=CreateMember(**member_dict)
            )

    return obj


def add_to_role(
        db: Session,
        member_uuid: UUID,
        *,
        role_uuid: UUID = None,
        role_discord_id: str = None,
        role_name: str = None
) -> bool:
    db_member = crud_member.get(db, uuid=member_uuid)

    if role_uuid:
        db_role = crud_role.get(db, uuid=role_uuid)
    elif role_discord_id:
        db_role = crud_role.get_by_discord(db, discord_id=role_discord_id)
    elif role_name:
        db_role = crud_role.get_by_name(db, name=role_name)
    else:
        raise ValueError(
            "Must have either role_uuid, role_discord_id or role_name!"
        )
    if db_role is None or db_member:
        return False

    db_member.roles.append(db_role)
    db.commit()

    return True
