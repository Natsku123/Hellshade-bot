from discord.ext import commands, tasks
from discord import Embed, Forbidden, HTTPException
from core.config import settings
from core.database import Session, session_lock
from core.database.crud.roles import role as role_crud
from core.database.crud.members import member as member_crud
from core.database.schemas.roles import UpdateRole, CreateRole
from core.database.utils import get_create_ctx, add_to_role, remove_from_role
from datetime import datetime

from core.utils import Colors


class Tools(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot

        # Start tasks
        self.role_update.start()

    @tasks.loop(minutes=30)
    async def role_update(self):
        """
        Update roles stored every 30 minutes
        :return:
        """
        async with session_lock:
            with Session() as session:

                # Get all roles that exist
                roles = role_crud.get_multi(
                    session, limit=role_crud.get_count(session)
                )

                # Parse roles into dict for "better performance"
                temp_roles = {}
                for role in roles:
                    temp_roles[role.discord_id] = role

                # Go through all roles visible
                for guild in self.__bot.guilds:
                    for r in guild.roles:

                        # Skip roles that are default or premium
                        if r.is_default or r.is_premium_subscriber:
                            continue

                        # Check that role is registered, otherwise skip
                        if r.id not in temp_roles:
                            continue

                        # If the name is the same, then skip
                        if r.name == temp_roles[r.id]:
                            continue

                        role_update = UpdateRole(**{
                            "name": r.name
                        })

                        # Update role
                        role_crud.update(
                            session, temp_roles[r.id], role_update
                        )

    @role_update.before_loop
    async def before_loop(self):
        await self.__bot.wait_until_ready()

    @commands.group(no_pm=True)
    async def role(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = Embed()
            embed.set_author(name=self.__bot.user.name,
                             url=settings.URL,
                             icon_url=self.__bot.user.avatar_url)
            embed.title("Invalid role command! `!help role` for more info")
            embed.timestamp = datetime.utcnow()
            await ctx.send(embed=embed)

    @role.command(pass_context=True, no_pm=True)
    async def add(self, ctx, name):
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
                        await ctx.author.add_roles(
                            [{"id": d_id}],
                            reason="Added through role add command."
                        )

                        embed.title = f"{ctx.author.name} has been " \
                                      f"added to {name}!"
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
    async def remove(self, ctx, name):
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
                        await ctx.author.remove_roles(
                            [{"id": d_id}],
                            reason="Removed through role remove command."
                        )

                        embed.title = f"{ctx.author.name} has been " \
                                      f"removed from {name}!"
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
    async def create(self, ctx, discord_id, description):
        """
        Create assignable role
        :param ctx: Context
        :param discord_id: Role Discord ID
        :param description: Description of role usage
        :return:
        """
        embed = Embed()
        embed.set_author(name=self.__bot.user.name,
                         url=settings.URL,
                         icon_url=self.__bot.user.avatar_url)
        async with session_lock:
            d_channel = self.__bot.get_channel(discord_id)
            with Session() as session:
                role = CreateRole(**{
                    "discord_id": discord_id,
                    "name": d_channel.name,
                    "description": description
                })

                db_role = role_crud.create(session, obj_in=role)
                embed.title = f"Role {db_role.name} created."
                embed.colour = Colors.success
        embed.timestamp = datetime.utcnow()
        await ctx.send(embed=embed)

    @role.command(pass_context=True, no_pm=True)
    async def update(self,ctx, discord_id, description):
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

                    embed.title = f"Role {db_role.name} updated."
                    embed.colour = Colors.success

        embed.timestamp = datetime.utcnow()
        await ctx.send(embed=embed)

    @role.command(pass_context=True, no_pm=True)
    async def delete(self, ctx, discord_id):
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
                    db_role = role_crud.remove(session, db_role.uuid)
                    embed.title = f"Role {db_role.name} removed."
                    embed.colour = Colors.success

        embed.timestamp = datetime.utcnow()
        await ctx.send(embed=embed)
