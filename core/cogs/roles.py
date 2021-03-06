from discord.ext import commands, tasks
from discord import Embed, Forbidden, HTTPException, utils
from core.config import settings, logger
from core.database import Session, session_lock
from core.database.crud.roles import role as role_crud, \
    role_emoji as emoji_crud
from core.database.crud.members import member as member_crud
from core.database.crud.servers import server as server_crud
from core.database.crud.players import player as player_crud
from core.database.schemas.roles import UpdateRole, CreateRole, CreateRoleEmoji
from core.database.schemas.servers import UpdateServer
from core.database.utils import get_create_ctx, add_to_role, remove_from_role
from datetime import datetime

from core.utils import Colors


class Roles(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot

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
                    db_player = player_crud.get_by_discord(
                        session, payload.member.id
                    )

                    # Stop if player not registered
                    if db_player is None:
                        logger.error(
                            f"Player not found for {payload.member.id}."
                        )
                        return

                    db_member = member_crud.get_by_ids(
                        session, db_player.uuid, server.uuid
                    )

                    # Stop if member not registered
                    if db_member is None:
                        logger.error(
                            f"Member not found for {payload.member.id}."
                        )
                        return

                    e = payload.emoji.name
                    emoji = emoji_crud.get_by_identifier(session, e)

                    if not emoji:
                        logger.error(
                            f"Emoji requested with {e} not "
                            f"found on {server.name}."
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
                        role = self.__bot.get_guild(payload.guild_id)\
                            .get_role(int(d_id))
                        await payload.member.add_roles(
                            role,
                            reason="Added through role reaction."
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
                    db_player = player_crud.get_by_discord(
                        session, payload.user_id
                    )

                    # Stop if player not registered
                    if db_player is None:
                        logger.error(
                            f"Player not found for {payload.user_id}."
                        )
                        return

                    db_member = member_crud.get_by_ids(
                        session, db_player.uuid, server.uuid
                    )

                    # Stop if member not registered
                    if db_member is None:
                        logger.error(
                            f"Member not found for {payload.user_id}."
                        )
                        return

                    e = payload.emoji.name
                    emoji = emoji_crud.get_by_identifier(session, e)

                    if not emoji:
                        logger.error(
                            f"Emoji requested with {e} not "
                            f"found on {server.name}."
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
                            role,
                            reason="Removed through role reaction."
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
                    roles = role_crud.get_multi_by_server_uuid(
                        session, server.uuid
                    )

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

                        role_update = UpdateRole(**{
                            "name": r.name
                        })

                        # Update role
                        role_crud.update(
                            session, temp_roles[r.id], role_update
                        )

                    # Update role message if it exists
                    if server.role_message is not None and \
                            server.role_channel is not None:
                        channel = self.__bot.get_channel(
                            int(server.role_channel)
                        )

                        # Continue if channel wasn't found
                        if channel is None:
                            logger.info(f"No channel found for {server.name}.")
                            continue

                        # Channel must not be bloated with messages
                        message = utils.find(
                            lambda m: (m.id == int(server.role_message)),
                            await channel.history(limit=10).flatten()
                        )

                        # Continue if message wasn't found
                        if message is None:
                            logger.info(f"No message found for {server.name}.")
                            continue

                        # Get context
                        ctx = await self.__bot.get_context(message)

                        embed = Embed()
                        embed.title = f"Assignable roles for " \
                                      f"**{message.guild.name}**"
                        embed.description = "Use reactions inorder to get " \
                                            "roles assigned to you, or use " \
                                            "`!role add roleName`"

                        converter = commands.EmojiConverter()
                        pconverter = commands.PartialEmojiConverter()

                        # Get all roles of a server
                        roles = role_crud.get_multi_by_server_uuid(
                            session, server.uuid
                        )

                        # Gather all used emojis for future reactions
                        emojis = []

                        for ro in roles:

                            emoji = emoji_crud.get_by_role(session, ro.uuid)

                            try:
                                # Convert into actual emoji
                                e = await converter.convert(
                                    ctx, emoji.identifier
                                )
                            except commands.EmojiNotFound:
                                # Try partial emoji instead
                                try:
                                    e = await pconverter.convert(
                                        ctx, emoji.identifier
                                    )
                                except commands.PartialEmojiConversionFailure:
                                    # Assume that it is an unicode emoji
                                    e = emoji.identifier

                            # Add to message
                            embed.add_field(
                                name=f"{str(e)}  ==  {ro.name}",
                                value=ro.description,
                                inline=False
                            )

                            emojis.append(e)

                        await message.edit(embed=embed)

                        # Check old reactions
                        old_emojis = []
                        for r in message.reactions:
                            old_emojis.append(r.emoji)

                        # Add new reactions to message
                        for e in emojis:
                            if e not in old_emojis:
                                await message.add_reaction(e)

                        logger.info(f"Message updated for {server.name}.")

    @commands.group(no_pm=True)
    async def role(self, ctx):
        """
        Role management, more on !help role

        :param ctx: Context
        :return:
        """
        if ctx.invoked_subcommand is None:
            embed = Embed()
            embed.set_author(name=self.__bot.user.name,
                             url=settings.URL,
                             icon_url=self.__bot.user.avatar_url)
            embed.title = "Invalid role command! `!help role` for more info"
            embed.timestamp = datetime.utcnow()
            await ctx.send(embed=embed)

    @role.command(pass_context=True, no_pm=True)
    async def add(self, ctx, name: str):
        """
        Assign role for author
        :param ctx: Context
        :param name: Role name
        :return:
        """
        embed = Embed()
        embed.set_author(name=self.__bot.user.name,
                         url=settings.URL,
                         icon_url=self.__bot.user.avatar_url)
        async with session_lock:
            with Session() as session:
                db_member = get_create_ctx(ctx, session, member_crud)

                found, d_id = add_to_role(
                    session, db_member.uuid, role_name=name
                )

                # If role is not found
                if not found:
                    embed.title = "This role is not assignable!"
                    embed.colour = Colors.error
                    embed.description = "This role doesn't exists or " \
                                        "it is not assignable."
                else:
                    try:
                        role = ctx.guild.get_role(int(d_id))
                        await ctx.author.add_roles(
                            role,
                            reason="Added through role add command."
                        )

                        embed.title = f"*{ctx.author.name}* has been " \
                                      f"added to *{name}*!"
                        embed.colour = Colors.success
                    except Forbidden:
                        embed.title = "I don't have a permission to do that :("
                        embed.colour = Colors.unauthorized
                        embed.description = "Give me a permission to manage" \
                                            " roles or give me a higher role."
                    except HTTPException:
                        embed.title = "Something happened, didn't succeed :/"
                        embed.colour = Colors.error

        embed.timestamp = datetime.utcnow()
        await ctx.send(embed=embed)

    @role.command(pass_context=True, no_pm=True)
    async def remove(self, ctx, name: str):
        """
        Remove role from author
        :param ctx: Context
        :param name: Role name
        :return:
        """
        embed = Embed()
        embed.set_author(name=self.__bot.user.name,
                         url=settings.URL,
                         icon_url=self.__bot.user.avatar_url)
        async with session_lock:
            with Session() as session:
                db_member = get_create_ctx(ctx, session, member_crud)

                success, d_id = remove_from_role(
                    session, db_member.uuid, role_name=name
                )

                if not success:
                    embed.title = "This role is not assignable!"
                    embed.colour = Colors.error
                    embed.description = "This role doesn't exists or " \
                                        "it is not assignable."
                else:
                    try:
                        role = ctx.guild.get_role(int(d_id))
                        await ctx.author.remove_roles(
                            role,
                            reason="Removed through role remove command."
                        )

                        embed.title = f"*{ctx.author.name}* has been " \
                                      f"removed from *{name}*!"
                        embed.colour = Colors.success
                    except Forbidden:
                        embed.title = "I don't have a permission to do that :("
                        embed.colour = Colors.unauthorized
                        embed.description = "Give me a permission to manage" \
                                            " roles or give me a higher role."
                    except HTTPException:
                        embed.title = "Something happened, didn't succeed :/"
                        embed.colour = Colors.error

        embed.timestamp = datetime.utcnow()
        await ctx.send(embed=embed)

    @role.command(pass_context=True, no_pm=True)
    @commands.has_permissions(administrator=True)
    async def create(
            self, ctx, discord_id: int, description: str, emoji: str = None
    ):
        """
        Create assignable role

        :param ctx: Context
        :param discord_id: Role Discord ID
        :param description: Description of role usage
        :param emoji: Emoji for assignment via reactions
        :return:
        """
        embed = Embed()
        embed.set_author(name=self.__bot.user.name,
                         url=settings.URL,
                         icon_url=self.__bot.user.avatar_url)
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
                    role = CreateRole(**{
                        "discord_id": discord_id,
                        "name": d_role.name,
                        "description": description,
                        "server_uuid": get_create_ctx(
                            ctx, session, server_crud
                        ).uuid
                    })

                    db_role = role_crud.create(session, obj_in=role)

                    if emoji is not None:
                        if hasattr(emoji, 'name'):
                            emoji = emoji.name
                            
                        db_e = CreateRoleEmoji(**{
                            "identifier": emoji,
                            "role_uuid": db_role.uuid
                        })
                        emoji_crud.create(session, obj_in=db_e)
                    else:
                        embed.description = "**Note**: Role was created" \
                                            " without an emoji, so it " \
                                            "cannot be assigned with " \
                                            "reactions!"

                    embed.title = f"Role *{db_role.name}* created."
                    embed.colour = Colors.success
        embed.timestamp = datetime.utcnow()
        await ctx.send(embed=embed)

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
        embed.set_author(name=self.__bot.user.name,
                         url=settings.URL,
                         icon_url=self.__bot.user.avatar_url)
        async with session_lock:
            with Session() as session:
                db_role = role_crud.get_by_discord(session, discord_id)
                if db_role is None:
                    embed.title = "Role not found"
                    embed.colour = Colors.error
                else:
                    role_update = UpdateRole(**{
                        "description": description
                    })

                    db_role = role_crud.update(
                        session, db_obj=db_role, obj_in=role_update
                    )

                    embed.title = f"Role *{db_role.name}* updated."
                    embed.colour = Colors.success

        embed.timestamp = datetime.utcnow()
        await ctx.send(embed=embed)

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
        embed.set_author(name=self.__bot.user.name,
                         url=settings.URL,
                         icon_url=self.__bot.user.avatar_url)
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

    @role.command(pass_context=True, no_pm=True)
    async def list(self, ctx):
        """
        Get all roles for current server

        :param ctx: Context
        :return:
        """
        embed = Embed()
        embed.set_author(name=self.__bot.user.name,
                         url=settings.URL,
                         icon_url=self.__bot.user.avatar_url)
        async with session_lock:
            with Session() as session:

                # Get server data
                server = get_create_ctx(ctx, session, server_crud)

                # Get roles for server
                roles = role_crud.get_multi_by_server_uuid(
                    session, server.uuid
                )

                embed.title = f"Roles for *{ctx.guild.name}*"
                embed.colour = Colors.success

                # List all roles for current server
                for role in roles:
                    embed.add_field(
                        name=role.name, value=role.description, inline=False
                    )

        embed.timestamp = datetime.utcnow()
        await ctx.send(embed=embed)

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
                embed.description = "Use reactions inorder to get " \
                                    "roles assigned to you, or use " \
                                    "`!role add roleName`"

                converter = commands.EmojiConverter()
                pconverter = commands.PartialEmojiConverter()

                # Get all roles on the server
                roles = role_crud.get_multi_by_server_uuid(
                    session, get_create_ctx(ctx, session, server_crud).uuid
                )

                # Gather all used emojis for future reactions
                emojis = []

                for r in roles:

                    emoji = emoji_crud.get_by_role(
                        session, r.uuid
                    )

                    if emoji is not None:

                        try:
                            # Convert into actual emoji
                            e = await converter.convert(
                                ctx, emoji.identifier
                            )
                        except commands.EmojiNotFound:
                            # Try partial emoji instead
                            try:
                                e = await pconverter.convert(
                                    ctx, emoji.identifier
                                )
                            except commands.PartialEmojiConversionFailure:
                                # Assume that it is an unicode emoji
                                e = emoji.identifier

                        # Add to message
                        embed.add_field(
                            name=f"{str(e)}  ==  {r.name}",
                            value=r.description,
                            inline=False
                        )

                        emojis.append(e)

                # Send message
                role_message = await ctx.send(embed=embed)

                # Add reaction to message with all used emojis
                for e in emojis:
                    await role_message.add_reaction(e)

                # Update server object to include role message data
                server_update = UpdateServer(**{
                    "role_message": str(role_message.id),
                    "role_channel": str(ctx.channel.id)
                })

                server_crud.update(
                    session, db_obj=db_server, obj_in=server_update
                )
