from nextcord import SlashOption
from nextcord.ext import commands, tasks
import nextcord
import datetime
import json
import asyncio
import math
from core.database import Session, session_lock
from core.config import settings, logger
from core.database.crud.servers import server as crud_server
from core.database.crud.players import player as crud_player
from core.database.crud.members import member as crud_member
from core.database.crud.levels import level as crud_level
from core.database.schemas.players import CreatePlayer
from core.database.schemas.servers import CreateServer
from core.database.schemas.members import CreateMember
from core.database.schemas.levels import CreateLevel
from core.database.schemas.commands import CreateCommand, UpdateCommand
from core.database.utils import get_create, get_create_ctx
from core.utils import progress_bar, level_exp, process_exp, get_admins, \
    Colors, next_weekday, gets_exp

import core.database.crud.commands


class Utility(commands.Cog):
    def __init__(self, bot, admins):
        self.__bot = bot
        self.__admins = admins

        # Start
        self.weekly_top5.start()
        self.online_experience.start()

    @commands.Cog.listener()
    async def on_server_join(self, server):
        async with session_lock:
            with Session() as session:
                get_create(
                    session, crud_server, obj_in=CreateServer(**{
                        "discord_id": str(server.id),
                        "name": server.name,
                        "server_exp": 0,
                        "channel": None
                    })
                )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        async with session_lock:
            with Session() as session:
                db_player = get_create(
                    session, crud_player, obj_in=CreatePlayer(**{
                        "discord_id": member.id,
                        "name": member.name,
                        "hidden": True
                    })
                )
                db_server = get_create(
                    session, crud_server, obj_in=CreateServer(**{
                        "discord_id": str(member.guild.id),
                        "name": member.guild.name,
                        "server_exp": 0,
                        "channel": None
                    })
                )
                get_create(
                    session, crud_member, obj_in=CreateMember(**{
                        "exp": 0,
                        "player_uuid": db_player.uuid,
                        "server_uuid": db_server.uuid,
                        "level_uuid": None
                    })
                )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != self.__bot.user.id and not message.author.bot:
            async with session_lock:
                with Session() as session:
                    db_server = get_create(
                        session, crud_server, obj_in=CreateServer(**{
                            "discord_id": str(message.guild.id),
                            "name": message.guild.name,
                            "server_exp": 0,
                            "channel": None
                        })
                    )
                    db_player = get_create(
                        session, crud_player, obj_in=CreatePlayer(**{
                            "discord_id": message.author.id,
                            "name": message.author.name,
                            "hidden": True
                        })
                    )

                    db_member = get_create(
                        session, crud_member, obj_in=CreateMember(**{
                            "exp": 0,
                            "player_uuid": db_player.uuid,
                            "server_uuid": db_server.uuid,
                            "level_uuid": None
                        })
                    )

                    if db_member.level is not None:
                        level_value = db_member.level.value + 1
                    else:
                        level_value = 1

                    next_level = get_create(
                        session, crud_level, obj_in=CreateLevel(**{
                            "value": level_value,
                            "exp": level_exp(level_value)
                        })
                    )

                    if db_member.exp + 25 < next_level.exp:
                        crud_member.update(
                            session, db_obj=db_member,
                            obj_in={"exp": db_member.exp + 25}
                        )
                    else:
                        db_member = crud_member.update(
                            session, db_obj=db_member, obj_in={
                                "exp": (db_member.exp + 25 - next_level.exp),
                                "level_uuid": next_level.uuid
                            }
                        )
                        if db_member.server.channel is not None:
                            embed = nextcord.Embed()
                            embed.set_author(name=self.__bot.user.name,
                                             url=settings.URL,
                                             icon_url=self.__bot.user.avatar.url)
                            embed.title = f"**{db_member.player.name}** " \
                                          f"leveled up!"
                            embed.description = f"**{db_member.player.name}" \
                                                f"** leveled up to level " \
                                                f"**{db_member.level.value}" \
                                                f"** by sending messages!"
                            embed.colour = 9942302

                            await self.__bot.get_channel(
                                int(db_member.server.channel)
                            ).send(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if not user.bot:
            async with session_lock:
                with Session() as session:
                    db_server = get_create(
                        session, crud_server, obj_in=CreateServer(**{
                            "discord_id": str(user.guild.id),
                            "name": user.guild.name,
                            "server_exp": 0,
                            "channel": None
                        })
                    )
                    db_player = get_create(
                        session, crud_player, obj_in=CreatePlayer(**{
                            "discord_id": user.id,
                            "name": user.name,
                            "hidden": True
                        })
                    )
                    db_member = get_create(
                        session, crud_member, obj_in=CreateMember(**{
                            "exp": 0,
                            "player_uuid": db_player.uuid,
                            "server_uuid": db_server.uuid,
                            "level_uuid": None
                        })
                    )

                    if db_member.level is not None:
                        level_value = db_member.level.value + 1
                    else:
                        level_value = 1

                    next_level = get_create(
                        session, crud_level, obj_in=CreateLevel(**{
                            "value": level_value,
                            "exp": level_exp(level_value)
                        })
                    )

                    if db_member.exp + 10 < next_level.exp:
                        crud_member.update(
                            session, db_obj=db_member,
                            obj_in={"exp": db_member.exp + 10}
                        )
                    else:
                        db_member = crud_member.update(
                            session, db_obj=db_member, obj_in={
                                "exp": (db_member.exp + 10 - next_level.exp),
                                "level_uuid": next_level.uuid
                            }
                        )
                        if db_member.server.channel is not None:
                            embed = nextcord.Embed()
                            embed.set_author(name=self.__bot.user.name,
                                             url=settings.URL,
                                             icon_url=self.__bot.user.avatar.url)
                            embed.title = f"**{db_member.player.name}** " \
                                          f"leveled up!"
                            embed.description = f"**{db_member.player.name}" \
                                                f"** leveled up to level " \
                                                f"**{db_member.level.value}" \
                                                f"** by reacting!"
                            embed.colour = 9942302

                            await self.__bot.get_channel(
                                int(db_member.server.channel)
                            ).send(embed=embed)

    @tasks.loop(hours=168)
    async def weekly_top5(self):
        await self.__bot.wait_until_ready()
        now = datetime.datetime.now()
        next_sat = next_weekday(now, 5).replace(hour=12, minute=0, second=0)

        delta = next_sat - now
        await asyncio.sleep(delta.total_seconds())
        async with session_lock:
            with Session() as session:
                for server in self.__bot.guilds:
                    server_obj = get_create(
                        session, crud_server, obj_in=CreateServer(**{
                            "discord_id": str(server.id),
                            "name": server.name,
                            "server_exp": 0,
                            "channel": None
                        })
                    )

                    if server_obj.channel is None:
                        continue

                    top_5 = crud_member.get_top(session, server_obj.uuid, 5)

                    embed = nextcord.Embed()
                    embed.title = f"Weekly TOP 5 on **{server_obj.name}**"
                    embed.description = f"More data can be found " \
                                        f"[here]({settings.URL}/servers/" \
                                        f"{server_obj.uuid})"
                    embed.url = f"{settings.URL}/servers/{server_obj.uuid}/top5"
                    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
                    embed.colour = 8161513
                    embed.set_author(name=self.__bot.user.name,
                                     url=settings.URL,
                                     icon_url=self.__bot.user.avatar.url)

                    for member in top_5:
                        embed.add_field(
                            name=f"**{member.player.name}**",
                            value=f"- LVL: **{member.level.value}** "
                                  f"- EXP: **{member.exp}**",
                            inline=False
                        )

                    await self.__bot.get_channel(int(server_obj.channel)). \
                        send(embed=embed)

    @tasks.loop(minutes=1)
    async def online_experience(self):
        await self.__bot.wait_until_ready()
        async with session_lock:
            with Session() as session:
                leveled_up = {}
                for member in filter(gets_exp, self.__bot.get_all_members()):
                    player_obj = get_create(
                        session, crud_player, obj_in=CreatePlayer(**{
                            "discord_id": member.id,
                            "name": member.name,
                            "hidden": True
                        })
                    )

                    server_obj = get_create(
                        session, crud_server, obj_in=CreateServer(**{
                            "discord_id": str(member.guild.id),
                            "name": member.guild.name,
                            "server_exp": 0,
                            "channel": None
                        })
                    )

                    member_obj = get_create(
                        session, crud_member, obj_in=CreateMember(**{
                            "exp": 0,
                            "player_uuid": player_obj.uuid,
                            "server_uuid": server_obj.uuid,
                            "level_uuid": None
                        })
                    )

                    base_exp = 5
                    special_multi = 1

                    now = datetime.datetime.now(datetime.timezone.utc)

                    # Weekend double voice experience
                    # Between Friday 15:00 -> Sunday 23:59 (UTC)
                    if now.weekday() > 4 or \
                            (now.weekday() == 4 and now.hour > 15):
                        special_multi = 2

                    exp = math.ceil(
                        special_multi * (len(member.voice.channel.members) /
                                         4 * base_exp)
                    )

                    if member_obj.level is not None:
                        next_level = crud_level.get_by_value(
                            session, member_obj.level.value + 1
                        )
                    else:
                        next_level = crud_level.get_by_value(
                            session, 1
                        )

                    if next_level is None and member_obj.level is not None:
                        member_dict = {
                            "exp": level_exp(member_obj.level.value + 1),
                            "value": member_obj.level.value + 1
                        }

                        next_level = crud_level.create(
                            CreateMember(**member_dict)
                        )

                    if member_obj.exp + exp < next_level.exp:
                        crud_member.update(
                            session, db_obj=member_obj, obj_in={
                                "exp": member_obj.exp + exp
                            }
                        )
                    else:
                        member_obj = crud_member.update(
                            session, db_obj=member_obj,
                            obj_in={
                                "exp":
                                    member_obj.exp + exp - next_level.exp,
                                "level_uuid": next_level.uuid
                            }
                        )
                        if server_obj.channel is not None:
                            if server_obj.channel in leveled_up:
                                leveled_up[server_obj.channel]. \
                                    append(member_obj)
                            else:
                                leveled_up[server_obj.channel] \
                                    = [member_obj]
                    crud_server.update(
                        session, db_obj=server_obj, obj_in={
                            "name": member.guild.name,
                            "server_exp": server_obj.server_exp + exp
                        }
                    )

                for channel in leveled_up:
                    embed = nextcord.Embed()
                    embed.set_author(name=self.__bot.user.name,
                                     url=settings.URL,
                                     icon_url=self.__bot.user.avatar.url)
                    if len(leveled_up) > 1:
                        embed.title = f"{len(leveled_up)} players leveled up!"
                        embed.description = f"{len(leveled_up)} players " \
                                            f"leveled up by being active on " \
                                            f"a voice channel."
                    else:
                        embed.title = f"1 player leveled up!"
                        embed.description = f"1 player leveled up by being " \
                                            f"active on a voice channel."

                    embed.colour = 9442302
                    for member in leveled_up[channel]:
                        embed.add_field(
                            name=member.player.name,
                            value=f"Leveled up to "
                                  f"**Level {member.level.value}**",
                            inline=False
                        )

                    await self.__bot.get_channel(int(channel)).send(
                        embed=embed)

                logger.debug("Experience calculated.")

    @commands.command(pass_context=True, hidden=True, no_pm=True)
    @commands.has_permissions(administrator=True)
    async def generate_levels(self, ctx, up_to=None):
        embed = nextcord.Embed()
        embed.set_author(name=self.__bot.user.name,
                         url=settings.URL,
                         icon_url=self.__bot.user.avatar.url)

        async with session_lock:
            with Session() as session:
                levels = crud_level.generate_many(
                    session, up_to
                )

        embed.title = "Levels generated."
        embed.description = f"Levels generated up to {len(levels)}!"
        embed.colour = Colors.other

        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed=embed)

    @commands.command(pass_context=True, hidden=True, no_pm=True)
    @commands.has_permissions(administrator=True)
    async def load_dump(self, ctx, filename=None):
        embed = nextcord.Embed()
        embed.set_author(name=self.__bot.user.name,
                         url=settings.URL,
                         icon_url=self.__bot.user.avatar.url)

        updated = []
        if filename is None:
            filename = "/members.dump.json"
        try:
            with open(filename, "r") as dump_file:
                data = json.load(dump_file)
        except OSError:
            embed.colour = Colors.unauthorized
            embed.title = "File not found!"
            embed.description = "Be sure that you inserted the right " \
                                "filename and you have copied the file " \
                                "into the container!"
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)
            return

        for member in data:
            async with session_lock:
                with Session() as session:
                    player_discord_id = member["player"]["discord_id"]
                    server_discord_id = member["server"]["discord_id"]
                    exp = int(member["exp"])
                    player = self.__bot.get_user(player_discord_id)
                    server = self.__bot.get_guild(server_discord_id)

                    db_player = crud_player.get_by_discord(
                        session, player_discord_id
                    )

                    if db_player is None:
                        if player is None and "name" in member["player"]:
                            name = member["player"]["name"]
                        elif player is None and "name" not in member[
                            "player"]:
                            name = "UNKNOWN"
                        else:
                            name = player.name
                        db_player = crud_player.create(
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
                            db_player = crud_player.update(
                                session, db_obj=db_player, obj_in={
                                    "hidden": hidden
                                }
                            )

                    db_server = crud_server.get_by_discord(
                        session, server_discord_id
                    )
                    if db_server is None:
                        if server is None and "name" in member["server"]:
                            name = member["server"]["name"]
                        elif server is None and "name" not in member[
                            "server"]:
                            name = "UNKNOWN"
                        else:
                            name = server.name

                        db_server = crud_server.create(
                            session, obj_in=CreateServer(**{
                                "discord_id": str(server_discord_id),
                                "name": name,
                                "server_exp": 0,
                                "channel": member["server"].get("channel")
                            })
                        )
                    else:
                        if db_server.channel != member["server"]. \
                                get("channel"):
                            db_server = crud_server.update(
                                session, db_obj=db_server, obj_in={
                                    "channel": member["server"].get(
                                        "channel")
                                }
                            )

                    db_member = crud_member.get_by_ids(
                        session, db_player.uuid, db_server.uuid
                    )

                    if "level_id" in member:
                        logger.debug(member["level_id"])
                    if "level_id" in member and member[
                        "level_id"] != "NULL":
                        current_level = int(member["level_id"])
                    else:
                        current_level = 0

                    current_level, exp = process_exp(current_level, exp)
                    if current_level > 0:
                        db_level = get_create(
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
                        db_member = crud_member.create(
                            session, obj_in=CreateMember(**{
                                "exp": exp,
                                "player_uuid": db_player.uuid,
                                "server_uuid": db_server.uuid,
                                "level_uuid": level_uuid
                            })
                        )
                    else:
                        db_member = crud_member.update(
                            session, db_obj=db_member, obj_in={
                                "level_uuid": level_uuid,
                                "exp": exp
                            }
                        )

                    updated.append(db_member)
        embed.colour = Colors.other
        embed.title = "Members loaded from dump file."
        embed.description = f"Members updated: {len(updated)}"
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed=embed)

    @commands.command(pass_context=True, hidden=True, no_pm=True)
    @commands.has_permissions(administrator=True)
    async def levels_channel(self, ctx, channel_id=None):
        embed = nextcord.Embed()
        embed.set_author(name=self.__bot.user.name,
                         url=settings.URL,
                         icon_url=self.__bot.user.avatar.url)

        async with session_lock:
            with Session() as session:
                if channel_id is not None and \
                        self.__bot.get_channel(
                            int(channel_id)) is not None:

                    server = get_create(
                        session, crud_server, obj_in=CreateServer(**{
                            "discord_id": str(ctx.guild.id),
                            "name": ctx.guild.name,
                            "server_exp": 0,
                            "channel": channel_id
                        })
                    )
                    if server.channel != channel_id:
                        crud_server.update(
                            session, db_obj=server, obj_in={
                                "channel": channel_id
                            }
                        )
                    embed.title = "Success"
                    embed.colour = Colors.success
                    embed.description = "Channel successfully registered."
                elif channel_id is not None and \
                        self.__bot.get_channel(int(channel_id)) is None:
                    embed.colour = Colors.error
                    embed.title = "Error"
                    embed.description = "Channel not found."
                else:
                    server = get_create(
                        session, crud_server, obj_in=CreateServer(**{
                            "discord_id": str(ctx.guild.id),
                            "name": ctx.guild.name,
                            "server_exp": 0,
                            "channel": None
                        })
                    )

                    embed.title = f"Levels channel for **{server.name}**"
                    if server.channel is not None:
                        embed.colour = Colors.other
                        channel = self.__bot.get_channel(int(server.channel))
                        embed.add_field(
                            name="Levels channel:", value=channel.name
                        )
                        embed.add_field(
                            name="Creation date:", value=channel.created_at
                        )
                    else:
                        embed.colour = Colors.unauthorized
                        embed.add_field(
                            name="Levels channel:",
                            value="No channel for levels."
                        )
                        embed.add_field(
                            name="Setup",
                            value="Create a new text channel and run this "
                                  "command with the channel_id as an argument."
                        )

        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed=embed)

    @commands.command(pass_context=True, hidden=True)
    @commands.has_permissions(administrator=True)
    async def get_user(self, ctx, user_id=None):
        embed = nextcord.Embed()
        embed.set_author(
            name=self.__bot.user.name, url=settings.URL,
            icon_url=self.__bot.user.avatar.url
        )
        if ctx.message.author.id not in await get_admins(self.__bot):
            embed.title = "Unauthorized"
            embed.colour = Colors.unauthorized
            embed.description = "You don't have permissions to use this " \
                                "command :/"
        else:
            if user_id is None:
                user = nextcord.utils.get(
                    self.__bot.get_all_members(), id=ctx.message.author.id
                )
            else:
                user = nextcord.utils.get(
                    self.__bot.get_all_members(), id=user_id
                )

            embed.colour = Colors.other
            embed.title = "User information"
            embed.description = "User information from Discord API."
            embed.add_field(name="Name", value="**{0.name}**".format(user))
            embed.add_field(name="Discriminator",
                            value="**{0.discriminator}**".format(user))
            embed.add_field(name="Bot", value="**{0.bot}**".format(user))

        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
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
            async with session_lock:
                with Session() as session:

                    server = get_create(
                        session, crud_server, obj_in=CreateServer(**{
                            "discord_id": str(ctx.guild.id),
                            "name": ctx.guild.name,
                            "server_exp": 0,
                            "channel": None
                        })
                    )
                    top_5 = crud_member.get_top(session, server.uuid, value)

                    embed = nextcord.Embed()
                    embed.title = f"**TOP {value}** on **{server.name}**"
                    embed.description = f"More data can be found [here]" \
                                        f"({settings.URL}/servers/{server.uuid})."
                    embed.url = f"{settings.URL}/servers/{server.uuid}/top5"
                    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
                    embed.colour = Colors.other
                    embed.set_author(name=self.__bot.user.name,
                                     url=settings.URL,
                                     icon_url=self.__bot.user.avatar.url)

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
                async with session_lock:
                    with Session() as session:

                        db_server = get_create(
                            session, crud_server, obj_in=CreateServer(**{
                                "discord_id": str(ctx.guild.id),
                                "name": ctx.guild.name,
                                "server_exp": 0,
                                "channel": None
                            })
                        )

                        db_player = get_create(
                            session, crud_player, obj_in=CreatePlayer(**{
                                "discord_id": str(ctx.message.author.id),
                                "name": ctx.message.author.name,
                                "hidden": True
                            })
                        )

                        member = get_create(
                            session, crud_member, obj_in=CreateMember(**{
                                "exp": 0,
                                "player_uuid": db_player.uuid,
                                "server_uuid": db_server.uuid,
                                "level_uuid": None
                            })
                        )

                        if member.level is not None:
                            next_level = get_create(
                                session, crud_level, obj_in=CreateLevel(**{
                                    "value": member.level.value + 1,
                                    "exp": level_exp(member.level.value + 1)
                                })
                            )
                        else:
                            next_level = get_create(
                                session, crud_level, obj_in=CreateLevel(**{
                                    "value": 1,
                                    "exp": level_exp(1)
                                })
                            )

                        embed = nextcord.Embed()
                        embed.title = f"**{member.player.name}** on " \
                                      f"**{member.server.name}**"
                        embed.description = f"More data can be found [here]" \
                                            f"({settings.URL}/players/" \
                                            f"{member.player.uuid})."
                        embed.url = f"{settings.URL}/players/" \
                                    f"{member.player.uuid}/server/" \
                                    f"{member.server.uuid}"
                        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
                        embed.colour = Colors.success
                        embed.set_author(name=self.__bot.user.name,
                                         url=settings.URL,
                                         icon_url=self.__bot.user.avatar.url)
                        # embed.add_field(
                        #     name=f"**Level {next_level.value - 1}**",
                        #     value=f"Experience: **{member.exp}/{next_level.exp}**",
                        #     inline=False)

                        # embed.add_field(
                        #     name=f"Progress: "
                        #          f"**{member.exp / next_level.exp * 100:.2f}%**",
                        #     value=f"`{progress_bar(member.exp, next_level.exp)}`")

                        embed.set_image(
                            url=f"{settings.URL}/api/level-image"
                                f"?name={ctx.author.name}"
                                f"&level={next_level.value - 1}"
                                f"&current_exp={member.exp}"
                                f"&needed_exp={next_level.exp}")

            if message != "" and embed is None:
                await ctx.send(message)
            else:
                await ctx.send(embed=embed)

    @nextcord.slash_command("register", "Register yourself to be shown on bot.hellshade.fi.")
    async def register(self, ctx: nextcord.Interaction):
        """
        Register yourself to be shown on bot.hellshade.fi.
        :param ctx:
        :return:
        """
        async with ctx.channel.typing():
            async with session_lock:
                with Session() as session:
                    player = get_create(
                        session, crud_player, obj_in=CreatePlayer(**{
                            "discord_id": str(ctx.user.id),
                            "name": ctx.user.name,
                            "hidden": False
                        })
                    )

                    if player.hidden:
                        crud_player.update(
                            session, db_obj=player, obj_in={'hidden': False}
                        )

                    embed = nextcord.Embed()
                    embed.set_author(name=self.__bot.user.name,
                                     url=settings.URL,
                                     icon_url=self.__bot.user.avatar.url)

                    embed.title = "Success!"
                    embed.description = f"You have successfully registered " \
                                        f"yourself. You are now shown on " \
                                        f"[{settings.URL}]({settings.URL})"
                    embed.colour = Colors.success

                    await ctx.send(embed=embed)

    @register.subcommand("steamid", "Register SteamID")
    async def register_steamid(self, ctx: nextcord.Interaction, steamid: str = SlashOption(
        name="steamid",
        description="SteamID to register",
        required=True,
    )):
        async with ctx.channel.typing():
            async with session_lock:
                with Session() as session:
                    player = get_create(
                        session, crud_player, obj_in=CreatePlayer(**{
                            "discord_id": str(ctx.user.id),
                            "name": ctx.user.name,
                            "hidden": False
                        })
                    )

                    crud_player.update(session, db_obj=player, obj_in={'steam_id': steamid})

                    embed = nextcord.Embed()
                    embed.set_author(
                        name=self.__bot.user.name,
                        url=settings.URL,
                        icon_url=self.__bot.user.avatar.url,
                    )
                    embed.title = "Success!"
                    embed.description = "Your SteamID has been updated!"
                    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
                    embed.colour = Colors.success
                    await ctx.send(embed=embed, ephemeral=True)

    @nextcord.slash_command("unregister", "Hides you from bot.hellshade.fi.")
    async def unregister(self, ctx: nextcord.Interaction):
        """
        Hides you from bot.hellshade.fi.
        :param ctx:
        :return:
        """
        async with ctx.channel.typing():
            async with session_lock:
                with Session() as session:
                    player = get_create(
                        session, crud_player, obj_in=CreatePlayer(**{
                            "discord_id": str(ctx.user.id),
                            "name": ctx.user.name,
                            "hidden": False
                        })
                    )

                    if not player.hidden:
                        crud_player.update(
                            session, db_obj=player, obj_in={'hidden': True}
                        )

                    embed = nextcord.Embed()
                    embed.set_author(name=self.__bot.user.name,
                                     url=settings.URL,
                                     icon_url=self.__bot.user.avatar.url)

                    embed.title = "Success!"
                    embed.description = f"yourself. You are now hidden from " \
                                        f"[{settings.URL}]({settings.URL})"
                    embed.colour = Colors.success

                    await ctx.send(embed=embed)

    @unregister.subcommand("steamid", "Remove SteamID")
    async def unregister_steamid(self, ctx: nextcord.Interaction):
        async with ctx.channel.typing():
            async with session_lock:
                with Session() as session:
                    player = get_create(
                        session, crud_player, obj_in=CreatePlayer(**{
                            "discord_id": str(ctx.user.id),
                            "name": ctx.user.name,
                            "hidden": False
                        })
                    )

                    crud_player.update(session, db_obj=player, obj_in={'steam_id': None})

                    embed = nextcord.Embed()
                    embed.set_author(
                        name=self.__bot.user.name,
                        url=settings.URL,
                        icon_url=self.__bot.user.avatar.url,
                    )
                    embed.title = "Success!"
                    embed.description = "Your SteamID has been removed!"
                    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
                    embed.colour = Colors.success
                    await ctx.send(embed=embed, ephemeral=True)

    @commands.group(pass_context=True, no_pm=True, hidden=True)
    @commands.has_permissions(administrator=True)
    async def slash_commands(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = nextcord.Embed()
            embed.set_author(name=self.__bot.user.name,
                             url=settings.URL,
                             icon_url=self.__bot.user.avatar.url)
            embed.title = "Invalid role command! `!help slash_commands` for more info"
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await ctx.send(embed=embed)

    @slash_commands.command(pass_context=True, no_pm=True, hidden=True)
    @commands.has_permissions(administrator=True)
    async def enable(self, ctx, command: str):
        embed = nextcord.Embed()
        embed.set_author(name=self.__bot.user.name,
                         url=settings.URL,
                         icon_url=self.__bot.user.avatar.url)

        async with session_lock:
            with Session() as session:
                db_server = get_create_ctx(ctx, session, crud_server)
                db_command = core.database.crud.commands.command.get_by_server_and_name(
                    session, db_server.uuid, command
                )
                if db_command is None:
                    db_command = core.database.crud.commands.command.create(
                        session,
                        obj_in=CreateCommand(**{
                            "name": command,
                            "server_uuid": db_server.uuid,
                            "status": True
                        })
                    )
                else:
                    db_command = core.database.crud.commands.command.update(
                        session,
                        db_obj=db_command,
                        obj_in=UpdateCommand(**{
                            "status": True
                        })
                    )

                embed.description = f"Command `{db_command.name}` enabled for `{db_server.name}`!"
                embed.colour = nextcord.Colour.green()

        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed=embed)

    @slash_commands.command(pass_context=True, no_pm=True, hidden=True)
    @commands.has_permissions(administrator=True)
    async def disable(self, ctx, command: str):
        embed = nextcord.Embed()
        embed.set_author(name=self.__bot.user.name,
                         url=settings.URL,
                         icon_url=self.__bot.user.avatar.url)

        async with session_lock:
            with Session() as session:
                db_server = get_create_ctx(ctx, session, crud_server)
                db_command = core.database.crud.commands.command.get_by_server_and_name(
                    session, db_server.uuid, command
                )
                if command is None:
                    db_command = core.database.crud.commands.command.create(
                        session,
                        obj_in=CreateCommand(**{
                            "name": command,
                            "server_uuid": db_server.uuid,
                            "status": False
                        })
                    )
                else:
                    db_command = core.database.crud.commands.command.update(
                        session,
                        db_obj=db_command,
                        obj_in=UpdateCommand(**{
                            "status": False
                        })
                    )

                embed.description = f"Command `{db_command.name}` disabled for `{db_server.name}`!"
                embed.colour = nextcord.Colour.green()

        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        await ctx.send(embed=embed)

    @nextcord.slash_command("ip", "Show your public IP")
    async def ip(self, ctx):
        message = ""
        async with ctx.message.channel.typing():
            embed = nextcord.Embed()
            embed.title = ""
            embed.url = f"{settings.URL}/api/ip"
            embed.timestamp = datetime.datetime.utcnow()
            embed.colour = Colors.success
            embed.set_author(name=self.__bot.user.name,
                             url=settings.URL,
                             icon_url=self.__bot.user.avatar.url)
            embed.set_image(url=f"{settings.URL}/api/ip")

        if message != "" and embed is None:
            await ctx.send(message)
        else:
            await ctx.send(embed=embed)
