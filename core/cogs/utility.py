from discord.ext import commands
import discord
import datetime
import json
from core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import settings
from core.database.crud.servers import server as crud_server
from core.database.crud.players import player as crud_player
from core.database.crud.members import member as crud_member
from core.database.crud.levels import level as crud_level
from core.database.schemas.players import CreatePlayer
from core.database.schemas.servers import CreateServer
from core.database.schemas.members import CreateMember
from core.database.schemas.levels import CreateLevel
from core.database.utils import get_create
from core.utils import progress_bar, level_exp, process_exp


class Utility(commands.Cog):
    def __init__(self, bot, admins):
        self.__bot = bot
        self.__admins = admins

    @commands.command(pass_context=True, hidden=True, no_pm=True)
    async def load_dump(self, ctx, filename=None):
        embed = discord.Embed()
        embed.set_author(name=self.__bot.user.name,
                         url=settings.URL,
                         icon_url=self.__bot.user.avatar_url)

        if ctx.message.author.id not in self.__admins:
            embed.title = "Unauthorized"
            embed.colour = 16312092
            embed.description = "You don't have permissions to use " \
                                "this command :/"
        else:
            updated = []
            if filename is None:
                filename = "/members.dump.json"
            try:
                with open(filename, "r") as dump_file:
                    data = json.load(dump_file)
            except OSError:
                embed.colour = 16312092
                embed.title = "File not found!"
                embed.description = "Be sure that you inserted the right " \
                                    "filename and you have copied the file " \
                                    "into the container!"
                embed.timestamp = datetime.datetime.utcnow()
                await ctx.send(embed=embed)
                return

            for member in data:
                async with AsyncSession(engine) as session:
                    player_discord_id = member["player"]["discord_id"]
                    server_discord_id = member["server"]["discord_id"]
                    exp = int(member["exp"])
                    player = self.__bot.get_user(player_discord_id)
                    server = self.__bot.get_guild(server_discord_id)

                    db_player = await crud_player.get_by_discord(
                        session, player_discord_id
                    )

                    if db_player is None:
                        if player is None and "name" in member["player"]:
                            name = member["player"]["name"]
                        elif player is None and "name" not in member["player"]:
                            name = "UNKNOWN"
                        else:
                            name = player.name
                        db_player = await crud_player.create(
                            session, obj_in=CreatePlayer(**{
                                "discord_id": player_discord_id,
                                "name": name,
                                "hidden": "hidden" in member["player"] and
                                          member["player"]["hidden"] == 1
                            })
                        )
                    else:
                        hidden = "hidden" in member["player"] and \
                                 member["player"]["hidden"] == 1
                        if hidden != db_player.hidden:
                            db_player = await crud_player.update(
                                session, db_obj=db_player, obj_in={
                                    "hidden": hidden
                                }
                            )

                    db_server = await crud_server.get_by_discord(
                        session, server_discord_id
                    )
                    if db_server is None:
                        if server is None and "name" in member["server"]:
                            name = member["server"]
                        elif server is None and "name" not in member["server"]:
                            name = "UNKNOWN"
                        else:
                            name = server.name

                        db_server = await crud_server.create(
                            session, obj_in=CreateServer(**{
                                "discord_id": server_discord_id,
                                "name": name,
                                "server_exp": 0,
                                "channel": member["server"].get("channel")
                            })
                        )
                    else:
                        if db_server.channel != member["server"].\
                                get("channel"):
                            db_server = await crud_server.update(
                                session, db_obj=db_server, obj_in={
                                    "channel": member["server"].get("channel")
                                }
                            )

                    db_member = await crud_member.get_by_ids(
                        session, db_player.uuid, db_server.uuid
                    )

                    if "level_id" in member:
                        current_level = int(member["level_id"])
                    else:
                        current_level = 0

                    current_level, exp = process_exp(current_level, exp)
                    if current_level > 0:
                        db_level = await get_create(
                            session, crud_level, obj_in=CreateLevel(**{
                                "value": current_level,
                                "exp": level_exp(current_level),
                                "title": None
                            })
                        )
                        level_uuid = db_level.uuid
                    else:
                        level_uuid = None

                    if db_member is None:
                        db_member = await crud_member.create(
                            session, obj_in=CreateMember(**{
                                "exp": exp,
                                "player_uuid": db_player.uuid,
                                "server_uuid": db_server.uuid,
                                "level_uuid": level_uuid
                            })
                        )
                    else:
                        db_member = await crud_member.update(
                            session, db_obj=db_member, obj_in={
                                "level_uuid": level_uuid,
                                "exp": exp
                            }
                        )

                    updated.append(db_member)
            embed.colour = 8161513
            embed.title = "Members loaded from dump file."
            embed.description = f"Members updated: {len(updated)}"
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

    @commands.command(pass_context=True, hidden=True, no_pm=True)
    async def levels_channel(self, ctx, channel_id=None):
        embed = discord.Embed()
        embed.set_author(name=self.__bot.user.name,
                         url=settings.URL,
                         icon_url=self.__bot.user.avatar_url)
        if ctx.message.author.id not in self.__admins:
            embed.title = "Unauthorized"
            embed.colour = 16312092
            embed.description = "You don't have permissions to use " \
                                "this command :/"
        else:
            async with AsyncSession(engine) as session:
                if channel_id is not None and \
                        self.__bot.get_channel(int(channel_id)) is not None:

                    server = await get_create(
                        session, crud_server, obj_in=CreateServer(**{
                            "discord_id": ctx.guild.id,
                            "name": ctx.guild.name,
                            "server_exp": 0,
                            "channel": channel_id
                        })
                    )
                    embed.title = "Success"
                    embed.colour = 1171983
                    embed.description = "Channel successfully registered."
                elif self.__bot.get_channel(int(channel_id)) is None and \
                        channel_id is not None:
                    embed.colour = 13632027
                    embed.title = "Error"
                    embed.description = "Channel not found."
                else:
                    server = await get_create(
                        session, crud_server, obj_in=CreateServer(**{
                            "discord_id": ctx.guild.id,
                            "name": ctx.guild.name,
                            "server_exp": 0,
                            "channel": None
                        })
                    )

                    embed.title = f"Levels channel for **{server.name}**"
                    if server.channel is not None:
                        embed.colour = 8161513
                        channel = self.__bot.get_channel(server.channel)
                        embed.add_field(
                            name="Levels channel:", value=channel.name
                        )
                        embed.add_field(
                            name="Creation date:", value=channel.created_at
                        )
                    else:
                        embed.colour = 16312092
                        embed.add_field(
                            name="Levels channel:",
                            value="No channel for levels."
                        )
                        embed.add_field(
                            name="Setup",
                            value="Create a new text channel and run this "
                                  "command with the channel_id as an argument."
                        )

        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

    @commands.command(pass_context=True, hidden=True)
    async def get_user(self, ctx, user_id=None):
        embed = discord.Embed()
        embed.set_author(
            name=self.__bot.user.name, url=settings.URL,
            icon_url=self.__bot.user.avatar_url
        )
        if ctx.message.author.id not in self.__admins:
            embed.title = "Unauthorized"
            embed.colour = 16312092
            embed.description = "You don't have permissions to use this " \
                                "command :/"
        else:
            if user_id is None:
                user = discord.utils.get(
                    self.__bot.get_all_members(), id=ctx.message.author.id
                )
            else:
                user = discord.utils.get(
                    self.__bot.get_all_members(), id=user_id
                )

            embed.colour = 8161513
            embed.title = "User information"
            embed.description = "User information from Discord API."
            embed.add_field(name="Name", value="**{0.name}**".format(user))
            embed.add_field(name="Discriminator",
                            value="**{0.discriminator}**".format(user))
            embed.add_field(name="Bot", value="**{0.bot}**".format(user))

        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed)

    @commands.command(pass_context=True, no_pm=True, aliases=["top5"])
    async def top(self, ctx, value=5):
        """
        Get Top N users with the most experience on this server.
        :param ctx:
        :param value: N
        :return:
        """
        async with ctx.message.channel.typing():
            async with AsyncSession(engine) as session:

                server = await get_create(
                    session, crud_server, obj_in=CreateServer(**{
                        "discord_id": ctx.guild.id,
                        "name": ctx.guild.name,
                        "server_exp": 0,
                        "channel": None
                    })
                )
                top_5 = await crud_member.get_top(session, server.uuid, value)

                embed = discord.Embed()
                embed.title = f"**TOP {value}** on **{server.name}**"
                embed.description = f"More data can be found [here]" \
                                    f"({settings.URL}/servers/{server.uuid})."
                embed.url = f"{settings.URL}/servers/{server.uuid}/top5"
                embed.timestamp = datetime.datetime.utcnow()
                embed.colour = 8161513
                embed.set_author(name=self.__bot.user.name, url=settings.URL,
                                 icon_url=self.__bot.user.avatar_url)

                for member in top_5:
                    if member.level is not None:
                        level_value = member.level.value
                    else:
                        level_value = 0

                    embed.add_field(name=f"**{member.player.name}**",
                                    value=f"- LVL: **{level_value}** "
                                          f"- EXP: **{member.exp}**",
                                    inline=False)

            await ctx.send(embed=embed)

    @commands.command(pass_context=True, aliases=["my_exp"])
    async def rank(self, ctx):
        """
        Get your current experience status on this server.
        :param ctx:
        :return:
        """
        async with ctx.message.channel.typing():
            message = ""
            if ctx.message.guild is None:
                message = "Please use this command on a server."
                embed = None
            else:

                async with AsyncSession(engine) as session:

                    db_server = await get_create(
                        session, crud_server, obj_in=CreateServer(**{
                            "discord_id": ctx.guild.id,
                            "name": ctx.guild.name,
                            "server_exp": 0,
                            "channel": None
                        })
                    )

                    db_player = await get_create(
                        session, crud_player, obj_in=CreatePlayer(**{
                            "discord_id": ctx.message.author.id,
                            "name": ctx.message.author.name,
                            "hidden": True
                        })
                    )

                    member = await get_create(
                        session, crud_member, obj_in=CreateMember(**{
                            "exp": 0,
                            "player_uuid": db_player.uuid,
                            "server_uuid": db_server.uuid,
                            "level_uuid": None
                        })
                    )

                    if member.level is not None:
                        next_level = await get_create(
                            session, crud_level, obj_in=CreateLevel(**{
                                "value": member.level.value+1,
                                "exp": level_exp(member.level.value+1)
                            })
                        )
                    else:
                        next_level = await get_create(
                            session, crud_level, obj_in=CreateLevel(**{
                                "value": 1,
                                "exp": level_exp(1)
                            })
                        )

                    embed = discord.Embed()
                    embed.title = f"**{member.player.name}** on " \
                                  f"**{member.server.name}**"
                    embed.description = f"More data can be found [here]" \
                                        f"({settings.URL}/players/" \
                                        f"{member.player.uuid})."
                    embed.url = f"{settings.URL}/players/" \
                                f"{member.player.uuid}/server/" \
                                f"{member.server.uuid}"
                    embed.timestamp = datetime.datetime.utcnow()
                    embed.colour = 1171983
                    embed.set_author(name=self.__bot.user.name,
                                     url=settings.URL,
                                     icon_url=self.__bot.user.avatar_url)
                    embed.add_field(
                        name=f"**Level {next_level.value-1}**",
                        value=f"Experience: **{member.exp}/{next_level.exp}**",
                        inline=False)

                    embed.add_field(
                        name=f"Progress: "
                             f"**{member.exp / next_level.exp * 100:.2f}%**",
                        value=f"`{progress_bar(member.exp, next_level.exp)}`")

            if message != "" and embed is None:
                await ctx.send(message)
            else:
                await ctx.send(embed=embed)

    @commands.command(pass_context=True)
    async def register(self, ctx):
        """
        Register yourself to be shown on bot.hellshade.fi.
        :param ctx:
        :return:
        """
        async with ctx.message.channel.typing():
            async with AsyncSession(engine) as session:
                player = await get_create(
                    session, crud_player, obj_in=CreatePlayer(**{
                        "discord_id": ctx.message.author.id,
                        "name": ctx.message.author.name,
                        "hidden": False
                    })
                )

                if player.hidden:
                    await crud_player.update(
                        session, db_obj=player, obj_in={'hidden': False}
                    )

                embed = discord.Embed()
                embed.set_author(name=self.__bot.user.name, url=settings.URL,
                                 icon_url=self.__bot.user.avatar_url)

                embed.title = "Success!"
                embed.description = f"You have successfully registered " \
                                    f"yourself. You are now shown on " \
                                    f"[{settings.URL}]({settings.URL})"
                embed.colour = 1171983

                await ctx.send(embed=embed)


def setup(bot, admins):
    bot.add_cog(Utility(bot, admins))
