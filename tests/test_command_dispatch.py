import asyncio
import json
from types import SimpleNamespace
from uuid import UUID

from core.config import settings
from core.database import Session
from core.database.crud.dota_guild import dota_guild as crud_dg
from core.database.crud.members import member as crud_member
from core.database.crud.players import player as crud_player
from core.database.crud.roles import role as crud_role
from core.database.crud.roles import role_emoji as crud_role_emoji
from core.database.crud.servers import server as crud_server
from core.database.schemas.dota_guild import CreateDotaGuild
from core.database.schemas.players import CreatePlayer
from core.database.schemas.roles import CreateRole, CreateRoleEmoji
from core.database.schemas.servers import CreateServer
from core.database.schemas.members import CreateMember
from core.database.utils import add_to_role, get_create
from tests.support.discord_harness import FakeChannel, FakeUser, get_application_command, invoke_command


def test_utility_register_command_dispatches_through_fake_interaction(utility_cog, interaction_factory):
    assert {command.name for command in utility_cog.application_commands} >= {"register"}

    register_command = get_application_command(utility_cog, "register")
    interaction = interaction_factory(456789, "alice")
    asyncio.run(invoke_command(register_command, utility_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert embed.title == "Success!"


def test_utility_register_steamid_command_dispatches_through_fake_interaction(utility_cog, interaction_factory):
    steamid_command = getattr(utility_cog, "register_steamid")
    interaction = interaction_factory(456789, "alice")
    asyncio.run(invoke_command(steamid_command, utility_cog, interaction, steamid="STEAM_1:1:12345"))

    assert interaction.sent_messages
    steam_embed = interaction.sent_messages[-1]["args"][0]
    assert steam_embed is not None
    assert steam_embed.title == "Success!"


def test_utility_unregister_command_dispatches_through_fake_interaction(utility_cog, interaction_factory):
    unregister_command = get_application_command(utility_cog, "unregister")
    interaction = interaction_factory(456789, "alice")
    asyncio.run(invoke_command(unregister_command, utility_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert embed.title == "Success!"


def test_utility_unregister_steamid_command_dispatches_through_fake_interaction(utility_cog, interaction_factory):
    unregister_steamid_command = getattr(utility_cog, "unregister_steamid")
    interaction = interaction_factory(456789, "alice")
    asyncio.run(invoke_command(unregister_steamid_command, utility_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert embed.title == "Success!"


def test_utility_ip_command_dispatches_through_fake_interaction(utility_cog, interaction_factory):
    ip_command = get_application_command(utility_cog, "ip")
    interaction = interaction_factory(456789, "alice")
    asyncio.run(invoke_command(ip_command, utility_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert embed.title == ""
    assert embed.url == f"{settings.URL}/ip"
    assert embed.image.url == f"{settings.URL}/ip"


def test_games_dota_command_dispatches_through_fake_interaction(games_cog, interaction_factory):
    assert {command.name for command in games_cog.application_commands} >= {"dota"}

    root_command = get_application_command(games_cog, "dota")
    interaction = interaction_factory(111222, "bob")
    asyncio.run(invoke_command(root_command, games_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "Dota root command" in embed.title


def test_games_dota_random_command_dispatches_through_fake_interaction(games_cog, interaction_factory):
    games_cog._Games__heroes = [{"name": "Anti-Mage", "link": "https://example.com/anti-mage.png"}]
    random_command = getattr(games_cog, "slash_dota_random")
    interaction = interaction_factory(111222, "bob")
    asyncio.run(invoke_command(random_command, games_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert embed.title == "You randomed..."


def test_games_dota_guild_command_dispatches_through_fake_interaction(games_cog, interaction_factory):
    guild_command = getattr(games_cog, "dota_guild")
    interaction = interaction_factory(111222, "bob")
    asyncio.run(invoke_command(guild_command, games_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "Dota guild root command" in embed.title


def test_roles_role_command_dispatches_deprecation_embed(roles_cog, interaction_factory):
    assert {command.name for command in roles_cog.application_commands} >= {"role"}

    role_command = get_application_command(roles_cog, "role")
    interaction = interaction_factory(987654, "carol")
    asyncio.run(invoke_command(role_command, roles_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "deprecated" in embed.title.lower()
    assert "onboarding" in embed.description.lower()


def test_roles_slash_role_command_dispatches_deprecation_embed(roles_cog, interaction_factory):
    interaction = interaction_factory(987654, "carol")
    asyncio.run(invoke_command(getattr(roles_cog, "slash_role"), roles_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "deprecated" in embed.title.lower()
    assert "onboarding" in embed.description.lower()


def test_roles_slash_create_command_persists_assignable_role(roles_cog, interaction_factory):
    interaction = interaction_factory(987654, "carol")
    interaction.guild = SimpleNamespace(id=777, name="Guild")
    interaction.channel = FakeChannel(channel_id=321)
    role = SimpleNamespace(id=123456, name="Test Role")

    asyncio.run(invoke_command(
        getattr(roles_cog, "slash_create"),
        roles_cog,
        interaction,
        role=role,
        description="For testing",
        emoji="🎉",
    ))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert embed.title == "Role *Test Role* created."

    with Session() as session:
        db_server = get_create(
            session,
            crud_server,
            obj_in=CreateServer(discord_id="777", name="Guild", server_exp=0, channel=None),
        )
        db_role = crud_role.get_by_discord(session, "123456")
        assert db_role is not None
        assert db_role.server_uuid == db_server.uuid
        assert crud_role_emoji.get_by_role(session, UUID(str(db_role.uuid))) is not None


def test_roles_slash_update_command_modifies_role_description(roles_cog, interaction_factory):
    with Session() as session:
        db_server = get_create(
            session,
            crud_server,
            obj_in=CreateServer(discord_id="888", name="Guild 2", server_exp=0, channel=None),
        )
        db_role = crud_role.create(
            session,
            obj_in=CreateRole(discord_id="222222", name="Role To Update", description="Old", server_uuid=db_server.uuid),
        )
        crud_role_emoji.create(session, obj_in=CreateRoleEmoji(identifier="x", role_uuid=db_role.uuid))

    interaction = interaction_factory(987654, "carol")
    asyncio.run(invoke_command(
        getattr(roles_cog, "slash_update"),
        roles_cog,
        interaction,
        role="222222",
        description="New description",
    ))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert embed.title == "Role *Role To Update* updated."

    with Session() as session:
        updated_role = crud_role.get_by_discord(session, "222222")
        assert updated_role is not None
        assert updated_role.description == "New description"


def test_roles_slash_delete_command_removes_assignable_role(roles_cog, interaction_factory):
    with Session() as session:
        db_server = get_create(
            session,
            crud_server,
            obj_in=CreateServer(discord_id="999", name="Guild 3", server_exp=0, channel=None),
        )
        db_role = crud_role.create(
            session,
            obj_in=CreateRole(discord_id="333333", name="Role To Delete", description="Old", server_uuid=db_server.uuid),
        )
        crud_role_emoji.create(session, obj_in=CreateRoleEmoji(identifier="y", role_uuid=db_role.uuid))

    interaction = interaction_factory(987654, "carol")
    asyncio.run(invoke_command(
        getattr(roles_cog, "slash_delete"),
        roles_cog,
        interaction,
        role=SimpleNamespace(id=333333, name="Role To Delete"),
    ))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert embed.title == "Role *Role To Delete* removed."

    with Session() as session:
        assert crud_role.get_by_discord(session, "333333") is None


def test_roles_slash_list_command_shows_server_roles(roles_cog, interaction_factory):
    with Session() as session:
        db_server = get_create(
            session,
            crud_server,
            obj_in=CreateServer(discord_id="111", name="Guild 4", server_exp=0, channel=None),
        )
        crud_role.create(
            session,
            obj_in=CreateRole(discord_id="444444", name="List Role", description="Shown", server_uuid=db_server.uuid),
        )

    interaction = interaction_factory(987654, "carol")
    interaction.guild = SimpleNamespace(id=111, name="Guild 4")
    asyncio.run(invoke_command(getattr(roles_cog, "slash_list"), roles_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert embed.title == "Roles for *Guild 4*"
    assert any(field.name == "List Role" for field in embed.fields)


def test_roles_slash_init_command_initializes_role_message(roles_cog, interaction_factory):
    with Session() as session:
        db_server = get_create(
            session,
            crud_server,
            obj_in=CreateServer(discord_id="222", name="Guild 5", server_exp=0, channel=None),
        )
        crud_role.create(
            session,
            obj_in=CreateRole(discord_id="555555", name="Init Role", description="Shown", server_uuid=db_server.uuid),
        )

    interaction = interaction_factory(987654, "carol")
    interaction.guild = SimpleNamespace(id=222, name="Guild 5")
    interaction.channel = FakeChannel(channel_id=555)
    asyncio.run(invoke_command(getattr(roles_cog, "slash_init"), roles_cog, interaction))

    assert interaction.sent_messages
    assert interaction.channel.messages
    with Session() as session:
        updated_server = crud_server.get_by_discord(session, "222")
        assert updated_server is not None
        assert updated_server.role_message is not None
        assert updated_server.role_channel == "555"


def test_utility_top_command_dispatches_through_fake_interaction(utility_cog, interaction_factory):
    interaction = interaction_factory(456789, "alice")
    interaction.guild = SimpleNamespace(id=77, name="Top Guild")

    asyncio.run(invoke_command(getattr(utility_cog, "top"), utility_cog, interaction, value=5))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert embed.title.startswith("**TOP 5**")


def test_utility_rank_command_dispatches_through_fake_interaction(utility_cog, interaction_factory):
    interaction = interaction_factory(456789, "alice")
    interaction.guild = SimpleNamespace(id=88, name="Rank Guild")

    asyncio.run(invoke_command(getattr(utility_cog, "rank"), utility_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "Rank Guild" in embed.title or "on" in embed.title.lower()


def test_utility_generate_levels_command_dispatches_through_fake_interaction(utility_cog, interaction_factory):
    interaction = interaction_factory(456789, "alice")

    asyncio.run(invoke_command(getattr(utility_cog, "generate_levels"), utility_cog, interaction, up_to=2))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert embed.title == "Levels generated."


def test_utility_load_dump_command_dispatches_through_fake_interaction(monkeypatch, utility_cog, interaction_factory, tmp_path):
    dump_path = tmp_path / "members.json"
    dump_path.write_text(json.dumps([{
        "player": {"discord_id": "9001", "name": "Dumped Player", "hidden": 0},
        "server": {"discord_id": "9002", "name": "Dumped Server", "channel": None},
        "exp": 0,
    }]))

    monkeypatch.setattr(utility_cog._Utility__bot, "get_user", lambda _discord_id: None)
    monkeypatch.setattr(utility_cog._Utility__bot, "get_guild", lambda _discord_id: None)

    interaction = interaction_factory(456789, "alice")
    asyncio.run(invoke_command(getattr(utility_cog, "load_dump"), utility_cog, interaction, filename=str(dump_path)))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert embed.title == "Members loaded from dump file."


def test_utility_levels_channel_command_dispatches_through_fake_interaction(monkeypatch, utility_cog, interaction_factory):
    interaction = interaction_factory(456789, "alice")
    interaction.guild = SimpleNamespace(id=99, name="Level Guild")
    monkeypatch.setattr(utility_cog._Utility__bot, "get_channel", lambda channel_id: FakeChannel(channel_id=channel_id))

    asyncio.run(invoke_command(getattr(utility_cog, "levels_channel"), utility_cog, interaction, channel_id="123"))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert embed.title == "Success"


def test_utility_get_user_command_dispatches_through_fake_interaction(monkeypatch, utility_cog, interaction_factory):
    async def fake_get_admins(_bot):
        return [123456]

    monkeypatch.setattr("core.cogs.utility.get_admins", fake_get_admins)
    utility_cog._Utility__bot.get_all_members = lambda: [FakeUser(id=123456, name="alice", bot=False)]

    interaction = interaction_factory(123456, "alice")
    asyncio.run(invoke_command(getattr(utility_cog, "get_user"), utility_cog, interaction, user_id=None))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert embed.title == "User information"


def test_utility_slash_commands_group_root_and_subcommands_dispatch(utility_cog, interaction_factory):
    interaction = interaction_factory(456789, "alice")
    interaction.guild = SimpleNamespace(id=100, name="Command Guild")
    interaction.invoked_subcommand = None

    asyncio.run(invoke_command(getattr(utility_cog, "slash_commands"), utility_cog, interaction))
    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert embed.title == "Use slash command instead"

    enable_handler = getattr(utility_cog, "enable")
    disable_handler = getattr(utility_cog, "disable")

    asyncio.run(invoke_command(enable_handler, utility_cog, interaction, command="register"))
    assert interaction.sent_messages[-1]["args"][0].description.startswith("Command `register` enabled")

    asyncio.run(invoke_command(disable_handler, utility_cog, interaction, command="register"))
    assert interaction.sent_messages[-1]["args"][0].description.startswith("Command `register` disabled")


def test_games_steam_command_group_root_dispatches_through_fake_interaction(games_cog, interaction_factory):
    interaction = interaction_factory(111222, "bob")
    interaction.invoked_subcommand = None
    asyncio.run(invoke_command(getattr(games_cog, "steam"), games_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "Invalid steam command" in embed.title


def test_games_steam_news_group_root_dispatches_through_fake_interaction(games_cog, interaction_factory):
    interaction = interaction_factory(111222, "bob")
    interaction.invoked_subcommand = None
    asyncio.run(invoke_command(getattr(games_cog, "steam_news"), games_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "Invalid steam news command" in embed.title


def test_games_steam_news_subscribe_command_dispatches_through_fake_interaction(games_cog, interaction_factory):
    interaction = interaction_factory(111222, "bob")
    interaction.message = SimpleNamespace(author=interaction.user, channel=FakeChannel(channel_id=321))

    asyncio.run(invoke_command(getattr(games_cog, "steam_news_subscribe"), games_cog, interaction, app_id=570))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "subscribed" in embed.title.lower()


def test_games_steam_news_clear_command_dispatches_through_fake_interaction(games_cog, interaction_factory):
    interaction = interaction_factory(111222, "bob")
    interaction.message = SimpleNamespace(author=interaction.user, channel=FakeChannel(channel_id=321))

    asyncio.run(invoke_command(getattr(games_cog, "steam_news_clear"), games_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "Cleared subscriptions" in embed.title


def test_games_play_game_command_handles_invalid_timeout(games_cog, interaction_factory):
    interaction = interaction_factory(111222, "bob")
    interaction.message = SimpleNamespace(author=SimpleNamespace(roles=[], mention="<@123>"), channel=FakeChannel(channel_id=321))
    interaction.mention = "<@123>"

    asyncio.run(invoke_command(getattr(games_cog, "play_game"), games_cog, interaction, game="cs", players=2, timeout="bad"))

    assert interaction.sent_messages
    assert interaction.sent_messages[-1]["args"][0] == "Invalid timeout value."


def test_games_dota_guild_add_command_dispatches_through_fake_interaction(monkeypatch, games_cog, interaction_factory):
    class FakeResponse:
        def __init__(self):
            self.status = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def json(self):
            return {"success": True, "summary": {"guild_info": {"guild_name": "Test Dota Guild"}}}

    class FakeClientSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def get(self, _url):
            return FakeResponse()

    monkeypatch.setattr("core.cogs.games.ClientSession", lambda *args, **kwargs: FakeClientSession())
    monkeypatch.setattr("core.cogs.games.settings.STEAM_API_KEY", "test-key")

    interaction = interaction_factory(111222, "bob")
    interaction.guild = SimpleNamespace(id=555, name="Dota Guild Server")
    role = SimpleNamespace(id=444, name="Guild Role")

    asyncio.run(invoke_command(getattr(games_cog, "dota_guild_add"), games_cog, interaction, guild_id=1234, role=role))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "has been linked" in embed.title.lower()


def test_games_dota_guild_info_command_dispatches_through_fake_interaction(monkeypatch, games_cog, interaction_factory):
    async def fake_get_guild_summary(_client, guild):
        return SimpleNamespace(
            guild_info=SimpleNamespace(
                guild_tag="TAG",
                guild_name="Guild Name",
                guild_description="Description",
                guild_motd="MOTD",
                created_timestamp=SimpleNamespace(timestamp=lambda: 1234567890),
            )
        )

    monkeypatch.setattr("core.cogs.games.get_guild_summary", fake_get_guild_summary)

    interaction = interaction_factory(111222, "bob")
    interaction.guild = SimpleNamespace(id=666, name="Dota Info Server")
    with Session() as session:
        db_server = get_create(
            session,
            crud_server,
            obj_in=CreateServer(discord_id="666", name="Dota Info Server", server_exp=0, channel=None),
        )
        crud_dg.create(
            session,
            obj_in=CreateDotaGuild(
                role_discord_id="444",
                name="Guild Name",
                server_uuid=db_server.uuid,
                guild_id=4321,
            ),
        )

    asyncio.run(invoke_command(getattr(games_cog, "dota_guild_info"), games_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "Guild Name" in embed.title


def test_roles_slash_add_command_assigns_assignable_role(roles_cog, interaction_factory):
    interaction = interaction_factory(987654, "carol")
    interaction.guild = SimpleNamespace(id=777, name="Guild")
    interaction.user.roles = []

    with Session() as session:
        db_server = get_create(
            session,
            crud_server,
            obj_in=CreateServer(discord_id="777", name="Guild", server_exp=0, channel=None),
        )
        crud_role.create(
            session,
            obj_in=CreateRole(discord_id="123456", name="Test Role", description="For testing", server_uuid=db_server.uuid),
        )

    asyncio.run(invoke_command(
        getattr(roles_cog, "slash_add"),
        roles_cog,
        interaction,
        role=SimpleNamespace(id=123456, name="Test Role"),
    ))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert embed.title == "*carol* has been added to *Test Role*!"
    assert "Test Role" in interaction.user.roles[0].name


def test_roles_slash_remove_command_removes_assignable_role(roles_cog, interaction_factory):
    interaction = interaction_factory(987654, "carol")
    interaction.guild = SimpleNamespace(id=888, name="Guild 2")
    interaction.user.roles = []

    with Session() as session:
        db_server = get_create(
            session,
            crud_server,
            obj_in=CreateServer(discord_id="888", name="Guild 2", server_exp=0, channel=None),
        )
        db_player = crud_player.create(
            session,
            obj_in=CreatePlayer(discord_id="987654", name="carol", hidden=False),
        )
        db_member = crud_member.create(
            session,
            obj_in=CreateMember(
                exp=0,
                player_uuid=db_player.uuid,
                server_uuid=db_server.uuid,
                level_uuid=None,
            ),
        )
        db_role = crud_role.create(
            session,
            obj_in=CreateRole(discord_id="654321", name="Role To Remove", description="For testing", server_uuid=db_server.uuid),
        )
        add_to_role(session, db_member.uuid, role_name=db_role.name)

    asyncio.run(invoke_command(
        getattr(roles_cog, "slash_remove"),
        roles_cog,
        interaction,
        role=SimpleNamespace(id=654321, name="Role To Remove"),
    ))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert embed.title == "*carol* has been removed from *Role To Remove*!"


def test_roles_text_add_command_dispatches_deprecation_embed(roles_cog, interaction_factory):
    interaction = interaction_factory(987654, "carol")
    asyncio.run(invoke_command(getattr(roles_cog, "add"), roles_cog, interaction, name="Test Role"))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "deprecated" in embed.title.lower()


def test_roles_text_remove_command_dispatches_deprecation_embed(roles_cog, interaction_factory):
    interaction = interaction_factory(987654, "carol")
    asyncio.run(invoke_command(getattr(roles_cog, "remove"), roles_cog, interaction, name="Test Role"))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "deprecated" in embed.title.lower()


def test_games_text_dota_random_command_dispatches_through_fake_interaction(monkeypatch, games_cog, interaction_factory):
    games_cog._Games__heroes = [{"name": "Axe", "link": "https://example.com/axe.png"}]
    monkeypatch.setattr("core.cogs.games.random.randint", lambda _a, _b: 0)

    interaction = interaction_factory(111222, "bob")
    asyncio.run(invoke_command(getattr(games_cog, "dota_random"), games_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert embed.title == "You randomed..."


def test_roles_text_role_group_root_dispatches_deprecation_embed(roles_cog, interaction_factory):
    interaction = interaction_factory(987654, "carol")
    interaction.invoked_subcommand = None
    asyncio.run(invoke_command(getattr(roles_cog, "role"), roles_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "deprecated" in embed.title.lower()


def test_roles_text_create_command_dispatches_deprecation_embed(roles_cog, interaction_factory):
    interaction = interaction_factory(987654, "carol")
    asyncio.run(
        invoke_command(
            getattr(roles_cog, "create"),
            roles_cog,
            interaction,
            discord_id=123456,
            description="Test",
            emoji="🎉",
        )
    )

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "deprecated" in embed.title.lower()


def test_roles_text_update_command_dispatches_deprecation_embed(roles_cog, interaction_factory):
    interaction = interaction_factory(987654, "carol")
    asyncio.run(
        invoke_command(
            getattr(roles_cog, "update"),
            roles_cog,
            interaction,
            discord_id=123456,
            description="Updated",
        )
    )

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "deprecated" in embed.title.lower()


def test_roles_text_delete_command_dispatches_deprecation_embed(roles_cog, interaction_factory):
    interaction = interaction_factory(987654, "carol")
    asyncio.run(
        invoke_command(
            getattr(roles_cog, "delete"),
            roles_cog,
            interaction,
            discord_id=123456,
        )
    )

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "deprecated" in embed.title.lower()


def test_roles_text_list_command_dispatches_deprecation_embed(roles_cog, interaction_factory):
    interaction = interaction_factory(987654, "carol")
    asyncio.run(invoke_command(getattr(roles_cog, "list"), roles_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "deprecated" in embed.title.lower()


def test_roles_text_init_command_dispatches_use_slash_embed(roles_cog, interaction_factory):
    interaction = interaction_factory(987654, "carol")
    asyncio.run(invoke_command(getattr(roles_cog, "init"), roles_cog, interaction))

    assert interaction.sent_messages
    embed = interaction.sent_messages[-1]["args"][0]
    assert embed is not None
    assert "use slash command" in embed.title.lower()
