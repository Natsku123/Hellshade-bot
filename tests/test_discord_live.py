import asyncio
from contextlib import suppress
import os
from types import SimpleNamespace

import nextcord
import pytest

from core.cogs.roles import Roles
from core.config import settings
from core.database import Session
from core.database.crud.members import member as crud_member
from core.database.crud.players import player as crud_player
from core.database.crud.roles import role as crud_role
from core.database.crud.roles import role_emoji as crud_role_emoji
from core.database.crud.servers import server as crud_server
from core.database.schemas.members import CreateMember
from core.database.schemas.players import CreatePlayer
from core.database.schemas.roles import CreateRole, CreateRoleEmoji
from core.database.schemas.servers import CreateServer, UpdateServer
from core.database.utils import get_create
from tests.support.discord_harness import FakeChannel, FakeInteraction, FakeUser, build_cog


def _require_live_test_guild_id() -> int:
    guild_id = os.getenv("TEST_GUILD_ID")
    if not guild_id:
        pytest.skip("TEST_GUILD_ID not configured for live Discord tests")

    try:
        return int(guild_id)
    except ValueError:
        pytest.skip("TEST_GUILD_ID must be an integer Discord guild ID")


async def _create_ready_client() -> tuple[nextcord.Client, asyncio.Task]:
    intents = nextcord.Intents(guilds=True, members=True)
    client = nextcord.Client(intents=intents)
    connect_task: asyncio.Task | None = None
    try:
        await asyncio.wait_for(client.login(settings.BOT_TOKEN), timeout=20)
        connect_task = asyncio.create_task(client.connect())
        await asyncio.wait_for(client.wait_until_ready(), timeout=30)
        return client, connect_task
    except Exception as exc:
        if connect_task is not None:
            connect_task.cancel()
            with suppress(asyncio.CancelledError):
                await connect_task
        await client.close()
        pytest.skip(
            f"Discord integration unavailable: {type(exc).__name__}: {exc!s}"
        )


async def _close_ready_client(client: nextcord.Client, connect_task: asyncio.Task) -> None:
    await client.close()
    connect_task.cancel()
    with suppress(asyncio.CancelledError):
        await connect_task


@pytest.mark.live
def test_role_add_and_remove_slash_commands_mutate_discord_member_roles():
    if not settings.BOT_TOKEN:
        pytest.skip("Discord bot token not configured")
    test_guild_id = _require_live_test_guild_id()

    async def _run() -> None:
        client, connect_task = await _create_ready_client()

        try:
            if not client.guilds:
                pytest.skip("Bot is not in any Discord guilds")

            guild = client.get_guild(test_guild_id)
            if guild is None:
                pytest.skip(f"Bot is not in configured TEST_GUILD_ID={test_guild_id}")

            target = guild.owner
            if target is None:
                pytest.skip("No guild owner available for role assignment")

            if guild.me is None or not guild.me.guild_permissions.manage_roles:
                pytest.skip("Bot cannot manage roles in this guild")

            role_name = f"copilot-test-role-{abs(hash(guild.id))}"
            temp_role = await guild.create_role(name=role_name, reason="test role")
            try:
                cog = build_cog(Roles)
                cog._Roles__bot = SimpleNamespace(
                    user=client.user,
                    get_guild=lambda guild_id: client.get_guild(guild_id),
                )

                with Session() as session:
                    db_server = get_create(
                        session,
                        crud_server,
                        obj_in=CreateServer(
                            discord_id=str(guild.id),
                            name=guild.name,
                            server_exp=0,
                            channel=None,
                        ),
                    )
                    db_player = get_create(
                        session,
                        crud_player,
                        obj_in=CreatePlayer(
                            discord_id=str(target.id),
                            name=target.name,
                            hidden=False,
                        ),
                    )
                    get_create(
                        session,
                        crud_member,
                        obj_in=CreateMember(
                            exp=0,
                            player_uuid=db_player.uuid,
                            server_uuid=db_server.uuid,
                            level_uuid=None,
                        ),
                    )

                    db_role = crud_role.create(
                        session,
                        obj_in=CreateRole(
                            discord_id=str(temp_role.id),
                            name=temp_role.name,
                            description="Temporary role for tests",
                            server_uuid=db_server.uuid,
                        ),
                    )
                    crud_role_emoji.create(
                        session,
                        obj_in=CreateRoleEmoji(
                            identifier="test_role",
                            role_uuid=db_role.uuid,
                        ),
                    )

                interaction = FakeInteraction(
                    user=FakeUser(id=target.id, name=target.name),
                    guild=guild,
                    channel=FakeChannel(),
                )
                await cog.slash_add(interaction, role=temp_role)

                updated_member = await guild.fetch_member(target.id)
                assert updated_member is not None
                assert temp_role in updated_member.roles

                await cog.slash_remove(interaction, role=temp_role)

                updated_member = await guild.fetch_member(target.id)
                assert updated_member is not None
                assert temp_role not in updated_member.roles
            finally:
                try:
                    member = guild.get_member(target.id)
                    if member is not None:
                        await member.remove_roles(temp_role, reason="cleanup")
                except Exception:
                    pass
                await temp_role.delete(reason="cleanup")
        finally:
            await _close_ready_client(client, connect_task)

    asyncio.run(_run())


@pytest.mark.live
def test_reaction_listener_adds_and_removes_roles_for_live_guild():
    if not settings.BOT_TOKEN:
        pytest.skip("Discord bot token not configured")
    test_guild_id = _require_live_test_guild_id()

    async def _run() -> None:
        client, connect_task = await _create_ready_client()

        try:
            if not client.guilds:
                pytest.skip("Bot is not in any Discord guilds")

            guild = client.get_guild(test_guild_id)
            if guild is None:
                pytest.skip(f"Bot is not in configured TEST_GUILD_ID={test_guild_id}")

            target = guild.owner
            if target is None:
                pytest.skip("No guild owner available for reaction role tests")

            if guild.me is None or not guild.me.guild_permissions.manage_roles:
                pytest.skip("Bot cannot manage roles in this guild")

            role_name = f"copilot-react-role-{abs(hash(guild.id))}"
            temp_role = await guild.create_role(name=role_name, reason="reaction test role")
            try:
                cog = build_cog(Roles)
                cog._Roles__bot = SimpleNamespace(
                    user=client.user,
                    get_guild=lambda guild_id: client.get_guild(guild_id),
                )

                with Session() as session:
                    db_server = get_create(
                        session,
                        crud_server,
                        obj_in=CreateServer(
                            discord_id=str(guild.id),
                            name=guild.name,
                            server_exp=0,
                            channel=None,
                        ),
                    )
                    crud_server.update(
                        session,
                        db_obj=db_server,
                        obj_in=UpdateServer(
                            **{
                                "role_message": str(1),
                                "role_channel": str(guild.text_channels[0].id if guild.text_channels else 0),
                            }
                        ),
                    )
                    db_player = get_create(
                        session,
                        crud_player,
                        obj_in=CreatePlayer(
                            discord_id=str(target.id),
                            name=target.name,
                            hidden=False,
                        ),
                    )
                    get_create(
                        session,
                        crud_member,
                        obj_in=CreateMember(
                            exp=0,
                            player_uuid=db_player.uuid,
                            server_uuid=db_server.uuid,
                            level_uuid=None,
                        ),
                    )
                    db_role = crud_role.create(
                        session,
                        obj_in=CreateRole(
                            discord_id=str(temp_role.id),
                            name=temp_role.name,
                            description="Temporary role for reaction tests",
                            server_uuid=db_server.uuid,
                        ),
                    )
                    crud_role_emoji.create(
                        session,
                        obj_in=CreateRoleEmoji(
                            identifier="reaction_test",
                            role_uuid=db_role.uuid,
                        ),
                    )

                    role_uuid = db_role.uuid
                    assert role_uuid is not None

                payload_add = SimpleNamespace(
                    member=target,
                    guild_id=guild.id,
                    message_id=1,
                    emoji=SimpleNamespace(name="reaction_test"),
                    user_id=target.id,
                )
                payload_remove = SimpleNamespace(
                    member=target,
                    guild_id=guild.id,
                    message_id=1,
                    emoji=SimpleNamespace(name="reaction_test"),
                    user_id=target.id,
                )

                await cog.on_raw_reaction_add(payload_add)
                updated_member = guild.get_member(target.id)
                assert updated_member is not None
                assert temp_role in updated_member.roles

                await cog.on_raw_reaction_remove(payload_remove)
                updated_member = guild.get_member(target.id)
                assert updated_member is not None
                assert temp_role not in updated_member.roles
            finally:
                try:
                    role_member = guild.get_member(target.id)
                    if role_member is not None:
                        await role_member.remove_roles(temp_role, reason="cleanup")
                except Exception:
                    pass
                await temp_role.delete(reason="cleanup")
        finally:
            await _close_ready_client(client, connect_task)

    asyncio.run(_run())
