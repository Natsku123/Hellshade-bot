import re

import nextcord.partial_emoji
from typing import Optional, Union
from nextcord.ext import commands, tasks, application_checks
from nextcord import Embed, Forbidden, HTTPException, utils, SlashOption

# from discord_ui import nextcord, SlashOption, AutocompleteInteraction, SlashPermission
from core.config import settings, logger
from core.database import Session, session_lock
from core.database.crud.roles import role as role_crud, role_emoji as emoji_crud
from core.database.crud import members
from core.database.crud.servers import server as server_crud
from core.database.crud import players
from core.database.schemas.roles import UpdateRole, CreateRole, CreateRoleEmoji
from core.database.schemas.servers import UpdateServer
from core.database.schemas.members import CreateMember
from core.database.schemas.players import CreatePlayer
from core.database.models import Member, Server, Player, Role
from core.database.utils import get_create_ctx, add_to_role, remove_from_role
from datetime import datetime

from core.utils import Colors


async def desync(it):
    for x in it:
        yield x


def like_role(
        l: list[Union[nextcord.Role, Role]], s: str
) -> list[Union[nextcord.Role, Role]]:
    if not s or s == "":
        return l

    return [x for x in l if s.lower() in x.name.lower()]


async def autocomplete_context(
        session: Session, ctx: nextcord.Interaction
) -> tuple[Optional[Server], Player, Optional[Member]]:
    server = server_crud.get_by_discord(session, ctx.guild.id)
    player = players.player.get_by_discord(session, ctx.user.id)
    if player is None:
        player = players.player.create(
            session,
            obj_in=CreatePlayer(
                discord_id=ctx.user.id, name=ctx.user.name, hidden=True
            ),
        )
    if server is None:
        return None, player, None
    member = members.member.get_by_ids(session, player.uuid, server.uuid)
    if member is None:
        member = members.member.create(
            session,
            obj_in=CreateMember(
                exp=0, player_uuid=player.uuid, server_uuid=server.uuid
            ),
        )

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
    with Session() as session:
        server, player, author = await autocomplete_context(session, ctx)

        if server is None:
            return []

        roles = role_crud.get_multi_by_query(session, server.uuid, value)
        return [
            (role.name, role.discord_id)
            async for role in desync(roles)
            if role not in author.roles
        ]


async def removable_roles(
        cog: commands.Cog, ctx: nextcord.Interaction, value: str
) -> list[tuple[str, Union[str, int]]]:
    """
    Get removable roles for server and member.

    :param cog: Cog
    :param ctx: Context
    :param value: Autocomplete current value
    :return: list of name-role pairs
    """

    logger.debug(f"{cog.qualified_name}")
    with Session() as session:
        server, player, author = await autocomplete_context(session, ctx)

        if server is None:
            return []

        return [
            (role.name, role.discord_id)
            async for role in desync(like_role(author.roles, value))
        ]


async def creatable_roles(
        cog: commands.Cog, ctx: nextcord.Interaction, value: str
) -> list[nextcord.Role]:
    """
    Get creatable roles for server.

    :param cog: Cog
    :param ctx: Context
    :param value: Autocomplete current value
    :return: list of name-role pairs
    """
    logger.debug(f"{cog.qualified_name}")
    with Session() as session:
        server, _, _ = await autocomplete_context(session, ctx)

        if server is None:
            return []

        roles = [
            role
            async for role in desync(like_role(ctx.guild.roles, value))
            if not role_crud.get_by_discord(session, role.id)
        ]

        return roles


async def deletable_roles(
        cog: commands.Cog, ctx: nextcord.Interaction, value: str
) -> list[tuple[str, Union[str, int]]]:
    """
    Get deletable roles for server.

    :param cog: Cog
    :param ctx: Context
    :param value: Autocomplete current value
    :return: list of name-role pairs
    """
    logger.debug(f"{cog.qualified_name}")
    with Session() as session:
        server, _, _ = await autocomplete_context(session, ctx)

        if server is None:
            return []

        roles = role_crud.get_multi_by_query(session, server.uuid, value)

        return [(role.name, role.discord_id) async for role in desync(roles)]


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
    with Session() as session:
        server, _, _ = await autocomplete_context(session, ctx)

        if server is None:
            # TODO make sure this returns ALL emojis usable on said Guild
            return [str(emoji) async for emoji in desync(ctx.guild.emojis)]

        roles = role_crud.get_multi_by_server_uuid(session, server.uuid)
        db_emojis = [
            emoji_crud.get_by_role(session, role.uuid).identifier
            for role in roles
            if emoji_crud.get_by_role(session, role.uuid)
        ]

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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        # Discard bot reaction event
        if payload.member.bot:
            return

        async with session_lock:
            with Session() as session:

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
                        role = self.__bot.get_guild(payload.guild_id).get_role(
                            int(d_id)
                        )
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
            with Session() as session:

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
                        role = guild.get_role(int(d_id))
                        await guild.get_member(payload.user_id).remove_roles(
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
            with Session() as session:

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

                        # Channel must not be bloated with messages
                        message = utils.find(
                            lambda m: (m.id == int(server.role_message)),
                            await channel.history(limit=10).flatten(),
                        )

                        # Continue if message wasn't found
                        if message is None:
                            logger.info(f"No message found for {server.name}.")
                            continue

                        # Get context
                        ctx = await self.__bot.get_context(message)

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

    @nextcord.slash_command("role", "Role management")
    async def slash_role(self, ctx: nextcord.Interaction):
        """
        Role management, more on !help role

        :param ctx: Context
        :return:
        """
        embed = Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        embed.title = "Invalid role command! `!help role` for more info"
        embed.timestamp = datetime.utcnow()
        await ctx.send(embed=embed, ephemeral=True)

    @commands.group(no_pm=True)
    async def role(self, ctx):
        """
        Role management, more on !help role

        :param ctx: Context
        :return:
        """
        if ctx.invoked_subcommand is None:
            embed = Embed()
            embed.set_author(
                name=self.__bot.user.name,
                url=settings.URL,
                icon_url=self.__bot.user.avatar.url,
            )
            embed.title = "Invalid role command! `!help role` for more info"
            embed.timestamp = datetime.utcnow()
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
        embed = Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        async with session_lock:
            with Session() as session:
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
                        await interaction.user.add_roles(
                            role, reason="Added through role add command."
                        )

                        embed.title = (
                            f"*{interaction.user.name}* has been "
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

        embed.timestamp = datetime.utcnow()
        await interaction.send(embed=embed, ephemeral=True)

    @role.command(pass_context=True, no_pm=True)
    async def add(self, ctx, name: str):
        """
        Assign role for author
        :param ctx: Context
        :param name: Role name
        :return:
        """
        embed = Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        async with session_lock:
            with Session() as session:
                db_member = get_create_ctx(ctx, session, members.member)

                found, d_id = add_to_role(session, db_member.uuid, role_name=name)

                # If role is not found
                if not found:
                    embed.title = "This role is not assignable!"
                    embed.colour = Colors.error
                    embed.description = (
                        "This role doesn't exists or " "it is not assignable."
                    )
                else:
                    try:
                        role = ctx.guild.get_role(int(d_id))
                        await ctx.author.add_roles(
                            role, reason="Added through role add command."
                        )

                        embed.title = (
                            f"*{ctx.author.name}* has been " f"added to *{name}*!"
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

        embed.timestamp = datetime.utcnow()
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
        embed = Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        async with session_lock:
            with Session() as session:
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
                        await interaction.user.remove_roles(
                            role, reason="Removed through role remove command."
                        )

                        embed.title = (
                            f"*{interaction.user.name}* has been "
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

        embed.timestamp = datetime.utcnow()
        await interaction.send(embed=embed, ephemeral=True)

    @role.command(pass_context=True, no_pm=True)
    async def remove(self, ctx, name: str):
        """
        Remove role from author
        :param ctx: Context
        :param name: Role name
        :return:
        """
        embed = Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        async with session_lock:
            with Session() as session:
                db_member = get_create_ctx(ctx, session, members.member)

                success, d_id = remove_from_role(
                    session, db_member.uuid, role_name=name
                )

                if not success:
                    embed.title = "This role is not assignable!"
                    embed.colour = Colors.error
                    embed.description = (
                        "This role doesn't exists or " "it is not assignable."
                    )
                else:
                    try:
                        role = ctx.guild.get_role(int(d_id))
                        await ctx.author.remove_roles(
                            role, reason="Removed through role remove command."
                        )

                        embed.title = (
                            f"*{ctx.author.name}* has been " f"removed from *{name}*!"
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

        embed.timestamp = datetime.utcnow()
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
        embed = Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        async with session_lock:
            with Session() as session:
                d_role = role
                db_role = role_crud.get_by_discord(session, str(d_role.id))

                if d_role is None:
                    embed.title = "Role not found."
                    embed.colour = Colors.error
                elif db_role is not None:
                    embed.title = "Role already exists!"
                    embed.colour = Colors.other
                else:
                    role = CreateRole(
                        **{
                            "discord_id": str(role.id),
                            "name": d_role.name,
                            "description": description,
                            "server_uuid": get_create_ctx(
                                interaction, session, server_crud
                            ).uuid,
                        }
                    )

                    db_role = role_crud.create(session, obj_in=role)

                    logger.debug(emoji)

                    if emoji is not None and not isinstance(
                            emoji, nextcord.partial_emoji.PartialEmoji
                    ):

                        if isinstance(emoji, str):
                            pattern = re.compile(r"<:(?P<name>\w+):(?P<id>\d+)>")
                            emoji = pattern.match(emoji).group("name")
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
        embed.timestamp = datetime.utcnow()
        await interaction.send(embed=embed, ephemeral=True)

    @role.command(pass_context=True, no_pm=True)
    @commands.has_permissions(administrator=True)
    async def create(self, ctx, discord_id: int, description: str, emoji: str = None):
        """
        Create assignable role

        :param ctx: Context
        :param discord_id: Role Discord ID
        :param description: Description of role usage
        :param emoji: Emoji for assignment via reactions
        :return:
        """
        embed = Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        async with session_lock:
            with Session() as session:
                d_role = ctx.guild.get_role(discord_id)
                db_role = role_crud.get_by_discord(session, discord_id)

                # TODO Add emoji parsing

                if d_role is None:
                    embed.title = "Role not found."
                    embed.colour = Colors.error
                elif db_role is not None:
                    embed.title = "Role already exists!"
                    embed.colour = Colors.other
                else:
                    role = CreateRole(
                        **{
                            "discord_id": discord_id,
                            "name": d_role.name,
                            "description": description,
                            "server_uuid": get_create_ctx(
                                ctx, session, server_crud
                            ).uuid,
                        }
                    )

                    db_role = role_crud.create(session, obj_in=role)

                    if emoji is not None:
                        converter = commands.EmojiConverter()
                        pconverter = commands.PartialEmojiConverter()

                        try:
                            # Convert into actual emoji
                            e = await converter.convert(ctx, emoji)
                        except commands.EmojiNotFound:
                            # Try partial emoji instead
                            try:
                                e = await pconverter.convert(ctx, emoji)
                            except commands.PartialEmojiConversionFailure:
                                # Assume that it is an unicode emoji
                                e = emoji
                    else:
                        e = None

                    if e is not None and not isinstance(
                            e, nextcord.partial_emoji.PartialEmoji
                    ):

                        if hasattr(e, "name"):
                            e = e.name

                        db_e = CreateRoleEmoji(
                            **{"identifier": e, "role_uuid": db_role.uuid}
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
        embed.timestamp = datetime.utcnow()
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
        embed = Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        async with session_lock:
            with Session() as session:
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

        embed.timestamp = datetime.utcnow()
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
        embed = Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        async with session_lock:
            with Session() as session:
                db_role = role_crud.get_by_discord(session, discord_id)
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

        embed.timestamp = datetime.utcnow()
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

        embed = Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        async with session_lock:
            with Session() as session:
                db_role = role_crud.get_by_discord(session, str(role.id))

                if db_role is None:
                    embed.title = "Role not found"
                    embed.colour = Colors.error
                else:
                    db_emoji = emoji_crud.get_by_role(session, db_role.uuid)

                    if db_emoji is not None:
                        emoji_crud.remove(session, uuid=db_emoji.uuid)

                    db_role = role_crud.remove(session, uuid=db_role.uuid)
                    embed.title = f"Role *{db_role.name}* removed."
                    embed.colour = Colors.success

        embed.timestamp = datetime.utcnow()
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
        embed = Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        async with session_lock:
            with Session() as session:
                db_role = role_crud.get_by_discord(session, discord_id)

                if db_role is None:
                    embed.title = "Role not found"
                    embed.colour = Colors.error
                else:
                    db_emoji = emoji_crud.get_by_role(session, db_role.uuid)

                    if db_emoji is not None:
                        emoji_crud.remove(session, uuid=db_emoji.uuid)

                    db_role = role_crud.remove(session, uuid=db_role.uuid)
                    embed.title = f"Role *{db_role.name}* removed."
                    embed.colour = Colors.success

        embed.timestamp = datetime.utcnow()
        await ctx.send(embed=embed)

    @slash_role.subcommand(name="list")
    async def slash_list(self, interaction: nextcord.Interaction):
        """
        Get all roles for current server

        :param interaction: Interaction
        :return:
        """
        embed = Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        async with session_lock:
            with Session() as session:
                # Get server data
                server = get_create_ctx(interaction, session, server_crud)

                # Get roles for server
                roles = role_crud.get_multi_by_server_uuid(session, server.uuid)

                embed.title = f"Roles for *{interaction.guild.name}*"
                embed.colour = Colors.success

                # List all roles for current server
                for role in roles:
                    embed.add_field(
                        name=role.name, value=role.description, inline=False
                    )

        embed.timestamp = datetime.utcnow()
        await interaction.send(embed=embed)

    @role.command(pass_context=True, no_pm=True)
    async def list(self, ctx):
        """
        Get all roles for current server

        :param ctx: Context
        :return:
        """
        embed = Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        async with session_lock:
            with Session() as session:
                # Get server data
                server = get_create_ctx(ctx, session, server_crud)

                # Get roles for server
                roles = role_crud.get_multi_by_server_uuid(session, server.uuid)

                embed.title = f"Roles for *{ctx.guild.name}*"
                embed.colour = Colors.success

                # List all roles for current server
                for role in roles:
                    embed.add_field(
                        name=role.name, value=role.description, inline=False
                    )

        embed.timestamp = datetime.utcnow()
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
            with Session() as session:
                db_server = get_create_ctx(interaction, session, server_crud)

                embed = Embed()
                embed.title = f"Assignable roles for **{interaction.guild.name}**"
                embed.description = (
                    "Use reactions inorder to get "
                    "roles assigned to you, or use "
                    "`!role add roleName`"
                )

                # Send message
                role_message = await interaction.send(embed=embed)
                role_message = await role_message.fetch()

                # Update server object to include role message data
                server_update = UpdateServer(
                    **{
                        "role_message": str(role_message.id),
                        "role_channel": str(interaction.channel.id),
                    }
                )

                server_crud.update(session, db_obj=db_server, obj_in=server_update)

                ctx = await self.__bot.get_context(role_message)

                converter = commands.EmojiConverter()
                pconverter = commands.PartialEmojiConverter()

                # Get all roles on the server
                roles = role_crud.get_multi_by_server_uuid(
                    session, get_create_ctx(interaction, session, server_crud).uuid
                )

                # Gather all used emojis for future reactions
                emojis = []

                for r in roles:

                    emoji = emoji_crud.get_by_role(session, r.uuid)

                    if emoji is not None:

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
        async with session_lock:
            with Session() as session:
                db_server = get_create_ctx(ctx, session, server_crud)

                embed = Embed()
                embed.title = f"Assignable roles for **{ctx.guild.name}**"
                embed.description = (
                    "Use reactions inorder to get "
                    "roles assigned to you, or use "
                    "`!role add roleName`"
                )

                converter = commands.EmojiConverter()
                pconverter = commands.PartialEmojiConverter()

                # Get all roles on the server
                roles = role_crud.get_multi_by_server_uuid(
                    session, get_create_ctx(ctx, session, server_crud).uuid
                )

                # Gather all used emojis for future reactions
                emojis = []

                for r in roles:

                    emoji = emoji_crud.get_by_role(session, r.uuid)

                    if emoji is not None:

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
                            name=f"{str(e)}  ==  {r.name}",
                            value=r.description,
                            inline=False,
                        )

                        emojis.append(e)

                # Send message
                role_message = await ctx.send(embed=embed)

                # Add reaction to message with all used emojis
                for e in emojis:
                    await role_message.add_reaction(e)

                # Update server object to include role message data
                server_update = UpdateServer(
                    **{
                        "role_message": str(role_message.id),
                        "role_channel": str(ctx.channel.id),
                    }
                )

                server_crud.update(session, db_obj=db_server, obj_in=server_update)
