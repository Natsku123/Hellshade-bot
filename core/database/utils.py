from typing import overload
from uuid import UUID

from nextcord import Interaction
from nextcord.ext.commands import Context
from sqlalchemy.orm import Session
from typing import Union, Tuple

from core.database.crud.servers import CRUDServer
from core.database.crud.servers import server as crud_server
from core.database.crud.players import CRUDPlayer
from core.database.crud.players import player as crud_player
from core.database.crud.members import CRUDMember
from core.database.crud.members import member as crud_member
from core.database.crud.levels import CRUDLevel
from core.database.crud.levels import level as crud_level
from core.database.crud.commands import command as crud_command
from core.database.crud.roles import role as crud_role
from core.database.schemas.servers import CreateServer
from core.database.schemas.players import CreatePlayer
from core.database.schemas.members import CreateMember
from core.database.schemas.levels import CreateLevel
from core.database.models import Server, Player, Member, Level

from core.utils import level_exp


@overload
def get_create(
    db: Session,
    crud: CRUDServer,
    *,
    obj_in: CreateServer,
) -> Server: ...


@overload
def get_create(
    db: Session,
    crud: CRUDPlayer,
    *,
    obj_in: CreatePlayer,
) -> Player: ...


@overload
def get_create(
    db: Session,
    crud: CRUDMember,
    *,
    obj_in: CreateMember,
) -> Member: ...


@overload
def get_create(
    db: Session,
    crud: CRUDLevel,
    *,
    obj_in: CreateLevel,
) -> Level: ...


def get_create(
    db: Session,
    crud: CRUDServer | CRUDPlayer | CRUDMember | CRUDLevel,
    *,
    obj_in: Union[CreateServer, CreatePlayer, CreateMember, CreateLevel],
) -> Union[Server, Player, Member, Level]:
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
        raise NotImplementedError

    return obj


def ensure_server_player_member(
        db: Session,
        *,
        guild_id: int,
        guild_name: str,
        player_id: int,
        player_name: str,
        hidden: bool = True,
) -> Tuple[Server, Player, Member]:
    """Get or create server, player and member in a single call."""

    db_server = get_create(
        db,
        crud_server,
        obj_in=CreateServer(
            discord_id=str(guild_id),
            name=guild_name,
            server_exp=0,
            channel=None,
        ),
    )

    db_player = get_create(
        db,
        crud_player,
        obj_in=CreatePlayer(
            discord_id=str(player_id),
            name=player_name,
            hidden=hidden,
        ),
    )

    db_member = get_create(
        db,
        crud_member,
        obj_in=CreateMember(
            exp=0,
            player_uuid=db_player.uuid,
            server_uuid=db_server.uuid,
            level_uuid=None,
        ),
    )

    return db_server, db_player, db_member


def ensure_server_player_member_ctx(
        ctx: Union[Context, Interaction],
        db: Session,
        *,
        hidden: bool = True,
) -> Tuple[Server, Player, Member]:
    """Get or create server, player and member from a Discord context."""

    guild = getattr(ctx, "guild", None)
    if guild is None:
        raise ValueError("Context must have a guild to get/create server.")

    user = getattr(ctx, "user", None)
    if user is None:
        user = getattr(ctx, "author", None)
    if user is None:
        raise ValueError("Context must have a user to get/create player.")

    return ensure_server_player_member(
        db,
        guild_id=guild.id,
        guild_name=guild.name,
        player_id=user.id,
        player_name=user.name,
        hidden=hidden,
    )


def get_create_ctx(
        ctx: Union[Context, Interaction], db: Session, crud, overrides=None
):
    """
    Create object if it doesn't exist with context
    :param ctx: Discord Context
    :param db: Database session
    :param crud: Crud-object to be used
    :param overrides: Override interfaces
    :return: object
    """

    if overrides is None:
        overrides = {}

    obj = None

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

    elif isinstance(crud, CRUDServer):
        if ctx.guild is None:
            raise ValueError("Context have a guild to get/create server!")

        obj = crud.get_by_discord(
            db, ctx.guild.id
        )

        if obj is None:
                obj = crud_server.create(
                    db,
                    obj_in=CreateServer(
                        discord_id=str(ctx.guild.id),
                        name=ctx.guild.name,
                        server_exp=overrides.get('exp', 0),
                        channel=str(overrides.get('channel_id'))
                        if overrides.get('channel_id') is not None
                        else None,
                    ),
                )

    elif isinstance(crud, CRUDPlayer):

        if hasattr(ctx, 'message') and ctx.message:
            obj = crud.get_by_discord(
                db, ctx.message.author.id
            )
        elif isinstance(ctx, Interaction):
            if ctx.user is None:
                raise ValueError("Context have a user to get/create player!")
            
            obj = crud.get_by_discord(
                db, ctx.user.id
            )
        else:
            obj = crud.get_by_discord(
                db, ctx.author.id
            )

        if obj is None:
            if hasattr(ctx, 'message') and ctx.message:
                player_dict = {
                    "discord_id": str(ctx.message.author.id),
                    "name": ctx.message.author.name,
                    "hidden": overrides.get('hidden', False)
                }
            elif isinstance(ctx, Interaction):
                if ctx.user is None:
                    raise ValueError("Context have a user to get/create player!")

                player_dict = {
                    "discord_id": str(ctx.user.id),
                    "name": ctx.user.name,
                    "hidden": overrides.get('hidden', False)
                }
            else:
                player_dict = {
                    "discord_id": str(ctx.author.id),
                    "name": ctx.author.name,
                    "hidden": overrides.get('hidden', False)
                }
            obj = crud_player.create(
                db, obj_in=CreatePlayer(**player_dict)
            )

    elif isinstance(crud, CRUDMember):
        player = get_create_ctx(ctx, db, crud_player)
        server = get_create_ctx(ctx, db, crud_server)

        obj = crud_member.get_by_ids(
            db, player.uuid, server.uuid
        )
        if obj is None:
            member_dict = {
                "exp": overrides.get('exp', 0),
                "player_uuid": player.uuid,
                "server_uuid": server.uuid,
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
        role_uuid: UUID | None = None,
        role_discord_id: str | None = None,
        role_name: str | None = None
) -> Tuple[bool, str]:
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
    if db_role is None or db_member is None:
        return False, ""

    db_member.roles.append(db_role)
    db.commit()

    return True, db_role.discord_id


def remove_from_role(
        db: Session,
        member_uuid: UUID,
        *,
    role_uuid: UUID | None = None,
    role_discord_id: str | None = None,
    role_name: str | None = None
) -> Tuple[bool, str]:
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
    if db_role is None or db_member is None:
        return False, ""

    if db_role not in db_member.roles:
        return False, ""

    db_member.roles.remove(db_role)
    db.commit()

    return True, db_role.discord_id


def get_guild_ids(command: str):
    with Session() as session:
        db_commands = crud_command.get_enabled_by_name(session, command)
        for c in db_commands:
            server = crud_server.get(session, c.uuid)
            if server is not None:
                yield int(server.discord_id)
