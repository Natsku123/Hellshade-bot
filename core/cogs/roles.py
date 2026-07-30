import re

import nextcord.partial_emoji
from typing import Optional, Sequence, Union, cast
from sqlalchemy.orm import Session
from nextcord.ext import commands, tasks, application_checks
from nextcord import Embed, Forbidden, HTTPException, utils, SlashOption
from uuid import UUID

# from discord_ui import nextcord, SlashOption, AutocompleteInteraction, SlashPermission
from core.config import settings, logger
from core.database import Session as SessionLocal, session_lock
from core.database.crud.roles import role as role_crud, role_emoji as emoji_crud
from core.database.crud import members
from core.database.crud.servers import server as server_crud
from core.database.crud import players
from core.database.schemas.roles import UpdateRole, CreateRole, CreateRoleEmoji
from core.database.schemas.servers import UpdateServer
from core.database.schemas.players import CreatePlayer
from core.database.models import Member, Server, Player, Role
from core.database.utils import (
    get_create_ctx,
    add_to_role,
    remove_from_role,
    ensure_server_player_member_ctx,
)
from datetime import datetime, timezone

from core.utils import Colors


async def desync(it):
    for x in it:
        yield x


def like_role(
    roles: Sequence[Union[nextcord.Role, Role]], s: str
) -> list[Union[nextcord.Role, Role]]:
    if not s or s == "":
        return list(roles)

    return [x for x in roles if s.lower() in x.name.lower()]


async def autocomplete_context(
    session: Session, ctx: nextcord.Interaction
) -> tuple[Optional[Server], Player, Optional[Member]]:
    if ctx.guild is None or ctx.user is None:
        player = players.player.create(
            session,
            obj_in=CreatePlayer(discord_id="0", name="UNKNOWN", hidden=True),
        )
        return None, player, None

    server, player, member = ensure_server_player_member_ctx(ctx, session, hidden=True)
    return server, player, member


async def assignable_roles(
        cog: commands.Cog, ctx: nextcord.Interaction, value: str
) -> list[tuple[str, Union[str, int]]]:
    """
    Get assignable roles for server and member.

    :param cog: Cog
    :param ctx: Context
    :param value: Autocomplete current value
    :return: list of name-role pairs
    """
    logger.debug(f"{cog.qualified_name}")
    with SessionLocal() as session:
        server, _, author = await autocomplete_context(session, ctx)

        if server is None or author is None:
            return []

        roles = role_crud.get_multi_by_query(session, server.uuid, value)

        return [(role.name, role.discord_id) for role in roles]


async def deletable_roles(
        cog: commands.Cog, ctx: nextcord.Interaction, value: str
) -> list[tuple[str, Union[str, int]]]:
    return await assignable_roles(cog, ctx, value)


async def available_emojis(
        cog: commands.Cog, ctx: nextcord.Interaction, value: str
) -> list[str]:
    """
    Get available emojis for bot and server.

    :param cog: Cog
    :param ctx: Context
    :param value: Autocomplete current value
    :return: list of name-emoji pairs
    """
    logger.debug(f"{cog.qualified_name}")
    logger.debug(value)
    with SessionLocal() as session:
        server, _, _ = await autocomplete_context(session, ctx)

        if ctx.guild is None:
            return []

        if server is None:
            # TODO make sure this returns ALL emojis usable on said Guild
            return [str(emoji) async for emoji in desync(ctx.guild.emojis)]

        roles = role_crud.get_multi_by_server_uuid(session, server.uuid)
        db_emojis = []
        for role in roles:
            emoji = emoji_crud.get_by_role(session, role.uuid)
            if emoji is not None:
                db_emojis.append(emoji.identifier)

        return [
            str(emoji)
            async for emoji in desync(ctx.guild.emojis)
            if emoji.name not in db_emojis
        ]


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.__bot = bot

        self.__rc = commands.RoleConverter()

        # Start tasks
        self.role_update.start()

    def _base_embed(self) -> Embed:
        embed = Embed()
        bot_user = cast(nextcord.ClientUser, self.__bot.user)
        embed.set_author(
            name=bot_user.name,
            url=settings.URL,
            icon_url=bot_user.avatar.url if bot_user.avatar else None,
        )
        return embed

    def _append_deprecation_notice(self, embed: Embed) -> Embed:
        note = (
            "⚠️ This slash command is deprecated. "
            "Please use onboarding instead."
        )
        if embed.description:
            embed.description = f"{embed.description}\n\n{note}"
        else:
            embed.description = note
        return embed

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        # Discard bot reaction event
        if payload.member.bot:
            return

        async with session_lock:
            with SessionLocal() as session:

                server = server_crud.get_by_discord(session, payload.guild_id)
                if server and str(payload.message_id) == server.role_message:
                    db_player = players.player.get_by_discord(
                        session, payload.member.id
                    )

                    # Stop if player not registered
                    if db_player is None:
                        logger.error(f"Player not found for {payload.member.id}.")
                        return

                    db_member = members.member.get_by_ids(
                        session, db_player.uuid, server.uuid
                    )

                    # Stop if member not registered
                    if db_member is None:
                        logger.error(f"Member not found for {payload.member.id}.")
                        return

                    e = payload.emoji.name
                    emoji = emoji_crud.get_by_identifier(session, e)

                    if not emoji:
                        logger.error(
                            f"Emoji requested with {e} not " f"found on {server.name}."
                        )
                        return

                    found, d_id = add_to_role(
                        session, db_member.uuid, role_uuid=emoji.role_uuid
                    )

                    # Stop if wasn't found
                    if not found:
                        logger.error(
                            f"Role not found for emoji {emoji.identifier} "
                            f"on {server.name}."
                        )
                        return

                    try:
                        guild = self.__bot.get_guild(payload.guild_id)
                        if guild is None:
                            return
                        role = guild.get_role(int(d_id))
                        if role is None:
                            return
                        await payload.member.add_roles(
                            role, reason="Added through role reaction."
                        )
                    except Forbidden:
                        logger.error(
                            "Forbidden: Not enough permissions to manage roles."
                        )
                    except HTTPException:
                        logger.error(
                            "HTTPException: Something went wrong while changing roles"
                        )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        async with session_lock:
            with SessionLocal() as session:

                server = server_crud.get_by_discord(session, payload.guild_id)
                if server and str(payload.message_id) == server.role_message:
                    db_player = players.player.get_by_discord(session, payload.user_id)

                    # Stop if player not registered
                    if db_player is None:
                        logger.error(f"Player not found for {payload.user_id}.")
                        return

                    db_member = members.member.get_by_ids(
                        session, db_player.uuid, server.uuid
                    )

                    # Stop if member not registered
                    if db_member is None:
                        logger.error(f"Member not found for {payload.user_id}.")
                        return

                    e = payload.emoji.name
                    emoji = emoji_crud.get_by_identifier(session, e)

                    if not emoji:
                        logger.error(
                            f"Emoji requested with {e} not " f"found on {server.name}."
                        )
                        return

                    found, d_id = remove_from_role(
                        session, db_member.uuid, role_uuid=emoji.role_uuid
                    )

                    # Stop if wasn't found
                    if not found:
                        logger.error(
                            f"Role not found for emoji {emoji.identifier} "
                            f"on {server.name}."
                        )
                        return

                    try:
                        guild = self.__bot.get_guild(payload.guild_id)
                        if guild is None:
                            return
                        role = guild.get_role(int(d_id))
                        member = guild.get_member(payload.user_id)
                        if role is None or member is None:
                            return
                        await member.remove_roles(
                            role, reason="Removed through role reaction."
                        )
                    except Forbidden:
                        logger.error(
                            "Forbidden: Not enough permissions to manage roles."
                        )
                    except HTTPException:
                        logger.error(
                            "HTTPException: Something went wrong while changing roles"
                        )

    @tasks.loop(minutes=30)
    async def role_update(self):
        """
        Update roles stored every 30 minutes
        :return:
        """
        await self.__bot.wait_until_ready()
        logger.info("Updating role messages...")

        async with session_lock:
            with SessionLocal() as session:

                # Go through all visible guilds
                for guild in self.__bot.guilds:

                    server = server_crud.get_by_discord(session, guild.id)

                    # Skip if server is not found
                    if server is None:
                        continue

                    # Get all roles for server
                    roles = role_crud.get_multi_by_server_uuid(session, server.uuid)

                    temp_roles = {}

                    for r in roles:
                        temp_roles[r.discord_id] = r

                    # Go through all roles of a guild
                    for r in guild.roles:

                        # Skip roles that are default or premium
                        if r.is_default or r.is_premium_subscriber:
                            continue

                        # Check that role is registered, otherwise skip
                        if r.id not in temp_roles:
                            continue

                        # If the name is the same, then skip
                        if r.name == temp_roles[r.id].name:
                            continue

                        role_update = UpdateRole(**{"name": r.name})

                        # Update role
                        role_crud.update(session, temp_roles[r.id], role_update)

                    # Update role message if it exists
                    if (
                            server.role_message is not None
                            and server.role_channel is not None
                    ):
                        channel = self.__bot.get_channel(int(server.role_channel))

                        # Continue if channel wasn't found
                        if channel is None:
                            logger.info(f"No channel found for {server.name}.")
                            continue

                        if not hasattr(channel, "history"):
                            logger.info(f"Channel for {server.name} has no history.")
                            continue

                        # Channel must not be bloated with messages
                        history = [
                            m async for m in cast(nextcord.TextChannel, channel).history(limit=10)
                        ]
                        message = utils.find(
                            lambda m: (m.id == int(server.role_message)),
                            history,
                        )

                        # Continue if message wasn't found
                        if message is None:
                            logger.info(f"No message found for {server.name}.")
                            continue

                        # Get context
                        ctx = await self.__bot.get_context(message)

                        if message.guild is None:
                            logger.info(f"Message guild missing for {server.name}.")
                            continue

                        embed = Embed()
                        embed.title = (
                            f"Assignable roles for " f"**{message.guild.name}**"
                        )
                        embed.description = (
                            "Use reactions inorder to get "
                            "roles assigned to you, or use "
                            "`!role add roleName`"
                        )

                        converter = commands.EmojiConverter()
                        pconverter = commands.PartialEmojiConverter()

                        # Get all roles of a server
                        roles = role_crud.get_multi_by_server_uuid(session, server.uuid)

                        # Gather all used emojis for future reactions
                        emojis = []

                        for ro in roles:

                            emoji = emoji_crud.get_by_role(session, ro.uuid)

                            if emoji is None:
                                continue

                            try:
                                # Convert into actual emoji
                                e = await converter.convert(ctx, emoji.identifier)
                            except commands.EmojiNotFound:
                                # Try partial emoji instead
                                try:
                                    e = await pconverter.convert(ctx, emoji.identifier)
                                except commands.PartialEmojiConversionFailure:
                                    # Assume that it is an unicode emoji
                                    e = emoji.identifier

                            # Add to message
                            embed.add_field(
                                name=f"{str(e)}  ==  {ro.name}",
                                value=ro.description,
                                inline=False,
                            )

                            emojis.append(e)

                        await message.edit(embed=embed)

                        # Check old reactions
                        old_emojis = []
                        for r in message.reactions:
                            old_emojis.append(r.emoji)

                        # Add new reactions to message
                        for e in emojis:
                            if isinstance(e, nextcord.partial_emoji.PartialEmoji):
                                logger.error(f"Emoji not cannot be used! Emoji: {e}")
                            elif e not in old_emojis:
                                await message.add_reaction(e)

                        logger.info(f"Message updated for {server.name}.")

    @nextcord.slash_command("role", "Deprecated role management. Use onboarding instead.")
    async def slash_role(self, ctx: nextcord.Interaction):
        """
        Role management, more on !help role

        :param ctx: Context
        :return:
        """
        embed = self._base_embed()
        embed.title = "Role commands are deprecated"
        embed.description = (
            "These role commands are no longer recommended. "
            "Please use onboarding instead."
        )
        embed.timestamp = datetime.now(timezone.utc)
        await ctx.send(embed=embed, ephemeral=True)

    @commands.group(no_pm=True)
    async def role(self, ctx):
        """
        Role management, more on !help role

        :param ctx: Context
        :return:
        """
        if ctx.invoked_subcommand is None:
            embed = self._base_embed()
            embed.title = "Role commands are deprecated"
            embed.description = (
                "Text role commands are deprecated. "
                "Please use onboarding instead."
            )
            embed.timestamp = datetime.now(timezone.utc)
            await ctx.send(embed=embed)

    @slash_role.subcommand(name="add")
    async def slash_add(
            self,
            interaction: nextcord.Interaction,
            role: nextcord.Role = SlashOption(
                name="role", description="Role to add.", required=True
            ),
    ):
        """
        Assign role for author
        :param role: Discord role to add
        :param interaction: Interaction
        :return:
        """
        embed = self._base_embed()
        async with session_lock:
            with SessionLocal() as session:
                db_member = get_create_ctx(interaction, session, members.member)

                found, d_id = add_to_role(
                    session, db_member.uuid, role_discord_id=str(role.id)
                )

                # If role is not found
                if not found:
                    embed.title = "This role is not assignable!"
                    embed.colour = Colors.error
                    embed.description = (
                        "This role doesn't exists or " "it is not assignable."
                    )
                else:
                    try:
                        user_member = cast(nextcord.Member, interaction.user)
                        await user_member.add_roles(
                            role, reason="Added through role add command."
                        )

                        embed.title = (
                            f"*{user_member.name}* has been "
                            f"added to *{role.name}*!"
                        )
                        embed.colour = Colors.success
                    except Forbidden:
                        embed.title = "I don't have a permission to do that :("
                        embed.colour = Colors.unauthorized
                        embed.description = (
                            "Give me a permission to manage"
                            " roles or give me a higher role."
                        )
                    except HTTPException:
                        embed.title = "Something happened, didn't succeed :/"
                        embed.colour = Colors.error

        self._append_deprecation_notice(embed)
        embed.timestamp = datetime.now(timezone.utc)
        await interaction.send(embed=embed, ephemeral=True)

    @role.command(pass_context=True, no_pm=True)
    async def add(self, ctx, name: str):
        """
        Assign role for author
        :param ctx: Context
        :param name: Role name
        :return:
        """
        embed = self._base_embed()
        embed.title = "Role command deprecated"
        embed.description = (
            "The role add command is deprecated. "
            "Please use onboarding instead."
        )
        embed.timestamp = datetime.now(timezone.utc)
        await ctx.send(embed=embed)

    @slash_role.subcommand(name="remove")
    async def slash_remove(
            self,
            interaction: nextcord.Interaction,
            role: nextcord.Role = SlashOption(
                name="role", description="Role to remove.", required=True
            ),
    ):
        """
        Remove role from author
        :param interaction: Interaction
        :param role: Discord role
        :return:
        """
        embed = self._base_embed()
        async with session_lock:
            with SessionLocal() as session:
                db_member = get_create_ctx(interaction, session, members.member)

                success, d_id = remove_from_role(
                    session, db_member.uuid, role_name=role.name
                )

                if not success:
                    embed.title = "This role is not assignable!"
                    embed.colour = Colors.error
                    embed.description = (
                        "You don't have this role, it doesn't exists or "
                        "it is not assignable."
                    )
                else:
                    try:
                        user_member = cast(nextcord.Member, interaction.user)
                        await user_member.remove_roles(
                            role, reason="Removed through role remove command."
                        )

                        embed.title = (
                            f"*{user_member.name}* has been "
                            f"removed from *{role.name}*!"
                        )
                        embed.colour = Colors.success
                    except Forbidden:
                        embed.title = "I don't have a permission to do that :("
                        embed.colour = Colors.unauthorized
                        embed.description = (
                            "Give me a permission to manage"
                            " roles or give me a higher role."
                        )
                    except HTTPException:
                        embed.title = "Something happened, didn't succeed :/"
                        embed.colour = Colors.error

        self._append_deprecation_notice(embed)
        embed.timestamp = datetime.now(timezone.utc)
        await interaction.send(embed=embed, ephemeral=True)

    @role.command(pass_context=True, no_pm=True)
    async def remove(self, ctx, name: str):
        """
        Remove role from author
        :param ctx: Context
        :param name: Role name
        :return:
        """
        embed = self._base_embed()
        embed.title = "Role command deprecated"
        embed.description = (
            "The role remove command is deprecated. "
            "Please use onboarding instead."
        )
        embed.timestamp = datetime.now(timezone.utc)
        await ctx.send(embed=embed)

    @slash_role.subcommand(name="create")
    @application_checks.has_permissions(administrator=True)
    async def slash_create(
            self,
            interaction: nextcord.Interaction,
            # role: str = SlashOption(
            #    name="role", description="Role to be made assignable.",
            #    required=True, autocomplete=True, autocomplete_callback=creatable_roles
            # ),
            role: nextcord.Role = SlashOption(
                name="role", description="Role to be made assignable.", required=True
            ),
            description: str = SlashOption(
                name="description",
                description="Describe the purpose of the role.",
                required=True,
            ),
            emoji: str = SlashOption(
                name="emoji", description="Emoji to be used with reactions.",
                required=False
            ),
    ):
        """
        Create assignable role

        :param interaction: Interaction
        :param role: Discord Role
        :param description: Description of role usage
        :param emoji: Emoji for assignment via reactions
        :return:
        """
        embed = self._base_embed()
        async with session_lock:
            with SessionLocal() as session:
                d_role = role
                db_role = role_crud.get_by_discord(session, str(d_role.id))

                if d_role is None:
                    embed.title = "Role not found."
                    embed.colour = Colors.error
                elif db_role is not None:
                    embed.title = "Role already exists!"
                    embed.colour = Colors.other
                else:
                    create_role = CreateRole(
                        **{
                            "discord_id": str(role.id),
                            "name": d_role.name,
                            "description": description,
                            "server_uuid": get_create_ctx(
                                interaction, session, server_crud
                            ).uuid,
                        }
                    )

                    db_role = role_crud.create(session, obj_in=create_role)

                    logger.debug(emoji)

                    if emoji is not None and not isinstance(
                            emoji, nextcord.partial_emoji.PartialEmoji
                    ):

                        if isinstance(emoji, str):
                            pattern = re.compile(r"<:(?P<name>\w+):(?P<id>\d+)>")
                            match = pattern.match(emoji)
                            if match is not None:
                                emoji = match.group("name")
                        elif hasattr(emoji, "name"):
                            emoji = emoji.name

                        db_e = CreateRoleEmoji(
                            **{"identifier": emoji, "role_uuid": db_role.uuid}
                        )
                        emoji_crud.create(session, obj_in=db_e)
                    elif isinstance(emoji, nextcord.partial_emoji.PartialEmoji):
                        embed.description = (
                            "**Note**: Role was created"
                            " without an emoji, because the bot "
                            "cannot use provided emoji..."
                        )
                    else:
                        embed.description = (
                            "**Note**: Role was created"
                            " without an emoji, so it "
                            "cannot be assigned with "
                            "reactions!"
                        )

                    embed.title = f"Role *{db_role.name}* created."
                    embed.colour = Colors.success
        self._append_deprecation_notice(embed)
        embed.timestamp = datetime.now(timezone.utc)
        await interaction.send(embed=embed, ephemeral=True)

    @role.command(pass_context=True, no_pm=True)
    @commands.has_permissions(administrator=True)
    async def create(self, ctx, discord_id: int, description: str, emoji: str | None = None):
        """
        Create assignable role

        :param ctx: Context
        :param discord_id: Role Discord ID
        :param description: Description of role usage
        :param emoji: Emoji for assignment via reactions
        :return:
        """
        embed = self._base_embed()
        embed.title = "Role command deprecated"
        embed.description = (
            "The role create command is deprecated. "
            "Please use onboarding instead."
        )
        embed.timestamp = datetime.now(timezone.utc)
        await ctx.send(embed=embed)

    @slash_role.subcommand(name="update")
    @application_checks.has_permissions(administrator=True)
    async def slash_update(
            self,
            interaction: nextcord.Interaction,
            role: str = SlashOption(
                name="role",
                description="Role to update.",
                required=True,
                autocomplete=True,
                autocomplete_callback=deletable_roles,
            ),
            description: str = SlashOption(
                name="description",
                description="Describe the purpose of the role.",
                required=True,
            ),
    ):
        """
        Update role description

        :param interaction: Interaction
        :param role: Discord Role
        :param description: New description of Role
        :return:
        """
        embed = self._base_embed()
        async with session_lock:
            with SessionLocal() as session:
                db_role = role_crud.get_by_discord(session, str(role))
                if db_role is None:
                    embed.title = "Role not found"
                    embed.colour = Colors.error
                else:
                    role_update = UpdateRole(**{"description": description})

                    db_role = role_crud.update(
                        session, db_obj=db_role, obj_in=role_update
                    )

                    embed.title = f"Role *{db_role.name}* updated."
                    embed.colour = Colors.success

        self._append_deprecation_notice(embed)
        embed.timestamp = datetime.now(timezone.utc)
        await interaction.send(embed=embed, ephemeral=True)

    @role.command(pass_context=True, no_pm=True)
    @commands.has_permissions(administrator=True)
    async def update(self, ctx, discord_id: int, description: str):
        """
        Update role description

        :param ctx: Context
        :param discord_id: Role Discord ID
        :param description: New description of Role
        :return:
        """
        embed = self._base_embed()
        embed.title = "Role command deprecated"
        embed.description = (
            "The role update command is deprecated. "
            "Please use onboarding instead."
        )
        embed.timestamp = datetime.now(timezone.utc)
        await ctx.send(embed=embed)

    @slash_role.subcommand(name="delete")
    @application_checks.has_permissions(administrator=True)
    async def slash_delete(
            self,
            interaction: nextcord.Interaction,
            role: nextcord.Role = SlashOption(
                name="role", description="Role to delete.", required=True
            ),
    ):
        """
        Delete assignable role

        :param interaction: Interaction
        :param role: Discord Role
        :return:
        """

        embed = self._base_embed()
        async with session_lock:
            with SessionLocal() as session:
                db_role = role_crud.get_by_discord(session, str(role.id))

                if db_role is None:
                    embed.title = "Role not found"
                    embed.colour = Colors.error
                else:
                    db_emoji = emoji_crud.get_by_role(session, UUID(db_role.uuid))
                    role_name = db_role.name

                    if db_emoji is not None:
                        emoji_crud.remove(session, uuid=db_emoji.uuid)

                    role_crud.remove(session, uuid=UUID(db_role.uuid))
                    embed.title = f"Role *{role_name}* removed."
                    embed.colour = Colors.success

        self._append_deprecation_notice(embed)
        embed.timestamp = datetime.now(timezone.utc)
        await interaction.send(embed=embed, ephemeral=True)

    @role.command(pass_context=True, no_pm=True)
    @commands.has_permissions(administrator=True)
    async def delete(self, ctx, discord_id: int):
        """
        Delete assignable role

        :param ctx: Context
        :param discord_id: Role Discord ID
        :return:
        """
        embed = self._base_embed()
        embed.title = "Role command deprecated"
        embed.description = (
            "The role delete command is deprecated. "
            "Please use onboarding instead."
        )
        embed.timestamp = datetime.now(timezone.utc)
        await ctx.send(embed=embed)

    @slash_role.subcommand(name="list")
    async def slash_list(self, interaction: nextcord.Interaction):
        """
        Get all roles for current server

        :param interaction: Interaction
        :return:
        """
        embed = self._base_embed()
        async with session_lock:
            with SessionLocal() as session:
                # Get server interfaces
                server = get_create_ctx(interaction, session, server_crud)

                guild = interaction.guild
                if guild is None:
                    return

                # Get roles for server
                roles = role_crud.get_multi_by_server_uuid(
                    session, server.uuid
                )

                embed.title = f"Roles for *{guild.name}*"
                embed.colour = Colors.success

                # List all roles for current server
                for role in roles:
                    embed.add_field(
                        name=role.name, value=role.description, inline=False
                    )

        self._append_deprecation_notice(embed)
        embed.timestamp = datetime.now(timezone.utc)
        await interaction.send(embed=embed, ephemeral=True)

    @role.command(pass_context=True, no_pm=True)
    async def list(self, ctx):
        """
        Get all roles for current server

        :param ctx: Context
        :return:
        """
        embed = self._base_embed()
        embed.title = "Role command deprecated"
        embed.description = (
            "The role list command is deprecated. "
            "Please use onboarding instead."
        )
        embed.timestamp = datetime.now(timezone.utc)
        await ctx.send(embed=embed)

    @slash_role.subcommand(name="init")
    @application_checks.has_permissions(administrator=True)
    async def slash_init(self, interaction: nextcord.Interaction):
        """
        Initialize role message for current channel

        :param interaction: Interaction
        :return:
        """

        async with session_lock:
            with SessionLocal() as session:
                db_server = get_create_ctx(interaction, session, server_crud)

                guild = interaction.guild
                channel = interaction.channel
                if guild is None or channel is None:
                    return

                embed = Embed()
                embed.title = f"Assignable roles for **{guild.name}**"
                embed.description = (
                    "Use reactions inorder to get "
                    "roles assigned to you, or use "
                    "`/role add`"
                )

                # Send message
                if not hasattr(channel, "send"):
                    await interaction.send(
                        "Current channel cannot receive messages.",
                        ephemeral=True,
                    )
                    return

                role_message = await cast(nextcord.TextChannel, channel).send(embed=embed)

                await interaction.send(
                    "Role message initialized in this channel.\n\n"
                    "⚠️ This slash command is deprecated. Please use onboarding instead.",
                    ephemeral=True,
                )

                # Update server object to include role message interfaces
                server_update = UpdateServer(
                    **{
                        "role_message": str(role_message.id),
                        "role_channel": str(channel.id),
                    }
                )

                server_crud.update(session, db_obj=db_server, obj_in=server_update)

                # Get all roles on the server
                roles = role_crud.get_multi_by_server_uuid(
                    session, UUID(get_create_ctx(interaction, session, server_crud).uuid)
                )

                # Gather all used emojis for future reactions
                emojis = []

                for r in roles:

                    emoji = emoji_crud.get_by_role(session, UUID(r.uuid))

                    if emoji is not None:
                        e = emoji.identifier

                        # Add to message
                        embed.add_field(
                            name=f"{str(e)}  ==  {r.name}",
                            value=r.description,
                            inline=False,
                        )

                        emojis.append(e)

                await role_message.edit(embed=embed)

                # Add reaction to message with all used emojis
                for e in emojis:
                    await role_message.add_reaction(e)

    @role.command(pass_context=True, no_pm=True, hidden=True)
    @commands.has_permissions(administrator=True)
    async def init(self, ctx):
        """
        Initialize role message for current channel

        :param ctx: Context
        :return:
        """
        embed = self._base_embed()
        embed.title = "Use slash command instead"
        embed.description = "Please use `/role init` to initialize the role message."
        embed.timestamp = datetime.now(timezone.utc)
        await ctx.send(embed=embed)
