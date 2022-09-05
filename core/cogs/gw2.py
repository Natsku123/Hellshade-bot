import asyncio
import random

import pygw2.core.models
from pygw2.api import Api

import nextcord
import datetime
import numpy
from uuid import UUID
from typing import Optional
from nextcord.ext import commands, tasks

from core.config import settings, logger
from core.database import Session, session_lock
from core.database.crud.gw2_api_key import gw2_api_key
from core.database.crud.gw2_guild import gw2_guild
from core.database.crud.gw2_guild_upgrade import gw2_guild_upgrade
from core.database.crud.gw2_daily_sub import gw2_daily_sub
from core.database.crud.players import player as player_crud
from core.database.crud.servers import server as server_crud
from core.database.models.gw2_daily_sub import DailyType
from core.database.models.gw2_guild import Gw2Guild
from core.database.schemas.gw2_api_key import CreateGw2ApiKey, UpdateGw2ApiKey
from core.database.schemas.gw2_guild import CreateGw2Guild, UpdateGw2Guild
from core.database.schemas.gw2_guild_upgrade import CreateGw2GuildUpgrade
from core.database.schemas.gw2_daily_sub import CreateGw2DailySub
from core.database.utils import get_create_ctx


def get_server_api_session(session: Session, interaction: nextcord.Interaction) -> Api:
    server = get_create_ctx(interaction, session, server_crud)
    gw2guild = gw2_guild.get_by_server_uuid(session, server.uuid)
    gw2apikey = gw2_api_key.get_by_player_uuid(session, gw2guild.guild_owner_uuid)
    return Api(api_key=gw2apikey.key)


def get_player_api_session(session: Session, interaction: nextcord.Interaction) -> Api:
    player = get_create_ctx(interaction, session, player_crud)
    gw2apikey = gw2_api_key.get_by_player_uuid(session, player.uuid)
    return Api(api_key=gw2apikey.key)


def get_server_guild(session: Session, interaction: nextcord.Interaction) -> Gw2Guild:
    server = get_create_ctx(interaction, session, server_crud)
    return gw2_guild.get_by_server_uuid(session, server.uuid)


async def get_available_guild_upgrades(api_session: Api, guild_id: str) -> tuple[list[str], list[str]]:
    """
    Get available guild upgrades for given guild with given api session

    :param api_session: GW2 API session
    :param guild_id: GW2 Guild ID
    :return: List of upgrade names
    """

    # Get Guild info
    guild_info = await api_session.guild(guild_id).get()

    # Get all available upgrades
    all_upgrades = numpy.array(await api_session.guild().upgrades())

    # Get already completed upgrades
    completed_upgrades = await api_session.guild(guild_id).upgraded()
    completed_upgrade_ids = [x.id for x in completed_upgrades if x.type is pygw2.core.models.GuildUpgradeType.Unlock]

    # Match all available upgrades
    available_upgrade_ids = list(all_upgrades[~numpy.isin(all_upgrades, completed_upgrade_ids)])
    available_upgrades = await api_session.guild().upgrades(*available_upgrade_ids)
    available_upgrades = numpy.array([x for x in available_upgrades if x.type is pygw2.core.models.GuildUpgradeType.Unlock and x.required_level and x.required_level <= guild_info.level])
    prerequisites_done = []

    # Filter upgrades to those that have prerequisites completed
    for x in available_upgrades:
        prerequisites = x.prerequisites
        if not isinstance(prerequisites, list):
            prerequisites = [prerequisites.id]

        else:
            prerequisites = [x.id for x in prerequisites]

        prerequisites_done.append(numpy.all(numpy.isin(prerequisites, completed_upgrade_ids)))

    # Return names and ids of the upgrades
    return [x.name for x in available_upgrades[prerequisites_done]], [x.id for x in available_upgrades[prerequisites_done]]


async def add_gw2_guild(db: Session, api_session: Api, name: str, server_uuid: UUID, owner_uuid: Optional[UUID] = None) -> Optional[Gw2Guild]:
    db_guild = gw2_guild.get_by_name(db, name)
    guild_data = await api_session.guild().search(name=name)

    if isinstance(guild_data, list) and len(guild_data) > 0:
        guild_data: pygw2.core.models.Guild = await api_session.guild(guild_data[0]).get()
    else:
        return None

    new_guild = {
        "name": guild_data.name,
        "server_uuid": server_uuid,
        "guild_gw2_id": guild_data.id
    }

    if owner_uuid is not None:
        new_guild["guild_owner_uuid"] = owner_uuid
    elif owner_uuid is not None and db_guild is not None:
        new_guild["guild_owner_uuid"] = db_guild.guild_owner_uuid

    if db_guild is None:
        db_guild = gw2_guild.create(db, obj_in=CreateGw2Guild(**new_guild))
    else:
        db_guild = gw2_guild.update(db, db_obj=db_guild, obj_in=UpdateGw2Guild(**new_guild))

    return db_guild


async def get_upgrade(api_session: Api, gw2guild_id: str, ids: str) -> dict:
    upgrades = await api_session.guild(guild_id=gw2guild_id).upgrades(ids)
    return upgrades


async def available_guild_upgrades(state: "Gw2", interaction: nextcord.Interaction, data: str) -> list[str]:
    with Session() as session:
        gw2guild = get_server_guild(session, interaction)

        if gw2guild.guild_gw2_id in state.upgrades and (state.upgrades[gw2guild.guild_gw2_id][0] - datetime.datetime.now()).total_seconds() < 60*40:
            available_upgrades = state.upgrades[gw2guild.guild_gw2_id][1]
        else:
            api_session = get_server_api_session(session, interaction)

            available_upgrades, available_upgrades_ids = await get_available_guild_upgrades(api_session, gw2guild.guild_gw2_id)

            state.upgrades[gw2guild.guild_gw2_id] = (datetime.datetime.now(), available_upgrades, available_upgrades_ids)

        if data != "":
            result = list(filter(lambda x: data.lower() in x.lower(), available_upgrades))
        else:
            result = available_upgrades

        if len(result) > 25:
            result = result[:25]

        return result


async def get_upgrade_status(api_session: Api, guild_id: str, upgrade_id: int):

    # Get Guild info
    guild = await api_session.guild(guild_id).get()

    # Get Upgrade info
    upgrade = await api_session.guild().upgrades(upgrade_id)

    # Get items in treasury
    treasure = numpy.array(await api_session.guild(guild_id).treasury())

    # Match costs to treasury
    cost_ids = [x.item_id for x in upgrade.costs if x.type is pygw2.core.models.GuildUpgradeCostType.Item]
    treasure_ids = [x.item_id for x in treasure]
    needed_treasures = treasure[numpy.isin(treasure_ids, cost_ids)]
    needed_treasures = {x.item_id: x for x in needed_treasures}

    # Get materials needed in text
    result_items = {x.name: (f"{needed_treasures[x.item_id].count if needed_treasures[x.item_id].count < x.count else x.count} / {x.count}" if x.item_id in needed_treasures else f"0 / {x.count}")
              for x in upgrade.costs if x.type is pygw2.core.models.GuildUpgradeCostType.Item}
    result_collectibles = {x.name: x.count for x in upgrade.costs if x.type is pygw2.core.models.GuildUpgradeCostType.Collectible or x.type is pygw2.core.models.GuildUpgradeCostType.Currency}

    if 'Guild Favor' in result_collectibles:
        result_collectibles['Guild Favor'] = f"{guild.favor if guild.favor < result_collectibles['Guild Favor'] else result_collectibles['Guild Favor']} / {result_collectibles['Guild Favor']}"
    if 'Aetherium' in result_collectibles:
        result_collectibles['Aetherium'] = f"{guild.aetherium if int(guild.aetherium) < int(result_collectibles['Aetherium']) else result_collectibles['Aetherium']} / {result_collectibles['Aetherium']}"

    return result_items | result_collectibles


class Gw2(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.__bot = bot
        self.upgrades: dict[str, tuple[datetime.datetime, list[str], list[str]]] = {}

        self.update_available_upgrades.start()
        self.upgrade_update.start()
        self.update_dailies.start()

    @tasks.loop(time=datetime.time(hour=0, minute=5))
    async def update_dailies(self):
        await self.__bot.wait_until_ready()

        api_session = Api()

        root_dailies = await api_session.achievements.daily()
        strikes = await api_session.achievements.categories(250)
        lws = await api_session.achievements.categories(238, 243, 330, 321)

        with Session() as session:
            # Go through all visible guilds
            for guild in self.__bot.guilds:
                server = server_crud.get_by_discord(session, guild.id)

                # Skip if server is not found
                if server is None:
                    continue

                daily_subs = gw2_daily_sub.get_by_server_uuid(session, server.uuid)

                for sub in daily_subs:
                    channel = self.__bot.get_channel(int(sub.channel_id))

                    # Channel must not be bloated with messages
                    message = nextcord.utils.find(
                        lambda m: (m.id == int(sub.message_id)),
                        await channel.history(limit=100).flatten(),
                    )

                    embed = nextcord.Embed()
                    embed.set_author(
                        name="Guild Wars 2 Dailies",
                        url=settings.URL,
                        icon_url="https://wiki.guildwars2.com/images/1/14/Daily_Achievement.png"
                    )
                    embed.timestamp = datetime.datetime.utcnow()

                    icon_url = None

                    if sub.daily_type == DailyType.PvE or sub.daily_type == DailyType.PvP or sub.daily_type == DailyType.WvW or sub.daily_type == DailyType.Fractals:
                        root_dailies = await api_session.achievements.daily()

                        if sub.daily_type == DailyType.PvE:
                            dailies = root_dailies.pve
                            title = "Daily PvE Achievements"
                        elif sub.daily_type == DailyType.PvP:
                            dailies = root_dailies.pvp
                            title = "Daily PvP Achievements"
                        elif sub.daily_type == DailyType.WvW:
                            dailies = root_dailies.wvw
                            title = "Daily WvW Achievements"
                        elif sub.daily_type == DailyType.Fractals:
                            dailies = root_dailies.fractals
                            title = "Daily Fractal Achievements"
                        else:
                            title = "Unknown"
                            dailies = []

                        if len(dailies) > 0:
                            icon_url = dailies[-1].achievement.icon

                        embed.title = title

                        description = ""
                        for d in dailies:
                            description += f"{d.achievement.name}\n"

                        embed.description = description

                    elif sub.daily_type == DailyType.Strikes:
                        strikes = await api_session.achievements.categories(250)
                        embed.title = "Daily Priority Strikes"
                        icon_url = strikes.icon

                        description = ""
                        for d in strikes.achievements:
                            description += f"{d.name}\n"

                        embed.description = description

                    elif sub.daily_type == DailyType.LivingWorld:
                        lws = await api_session.achievements.categories(238, 243, 330,
                                                                        321)
                        embed.title = "Daily Living World"
                        icons = [x.icon for x in lws if x.icon is not None]

                        icon_url = random.choice(icons)

                        description = ""

                        for c in lws:
                            description += f"**{c.name}**\n"
                            for d in c.achievements:
                                description += f"{d.name}\n"
                            description += "\n"

                        embed.description = description

                    if icon_url is None:
                        icon_url = "https://wiki.guildwars2.com/images/1/14/Daily_Achievement.png"

                    embed.set_thumbnail(icon_url)
                    await message.edit(embed=embed)

    @tasks.loop(time=datetime.time(hour=0, minute=0))
    async def delete_completed_upgrades(self):
        await self.__bot.wait_until_ready()

        async with session_lock:
            with Session() as session:

                # Go through all visible guilds
                for guild in self.__bot.guilds:
                    server = server_crud.get_by_discord(session, guild.id)

                    # Skip if server is not found
                    if server is None:
                        continue

                    gw2guild = gw2_guild.get_by_server_uuid(session, server.uuid)

                    # Skip if GW2 Guild is not found on server
                    if gw2guild is None or gw2guild.guild_upgrade_channel is None:
                        continue

                    channel = self.__bot.get_channel(int(gw2guild.guild_upgrade_channel))

                    # Continue if channel wasn't found
                    if channel is None:
                        logger.info(
                            f"No guild upgrades channel found for {server.name}.")
                        continue

                    completed = gw2_guild_upgrade.get_completed_by_guild_uuid(session, gw2guild.uuid)

                    for i, upgrade in enumerate(completed):

                        # Channel must not be bloated with messages
                        message = nextcord.utils.find(
                            lambda m: (m.id == int(upgrade.message_id)),
                            await channel.history(limit=100).flatten(),
                        )

                        # Skip if message wasn't found
                        if message is None:
                            continue

                        await message.delete(delay=0.1*i)
                        gw2_guild_upgrade.remove(session, uuid=gw2guild.uuid)

    @tasks.loop(minutes=30)
    async def upgrade_update(self):
        await self.__bot.wait_until_ready()

        async with session_lock:
            with Session() as session:

                # Go through all visible guilds
                for guild in self.__bot.guilds:
                    server = server_crud.get_by_discord(session, guild.id)

                    # Skip if server is not found
                    if server is None:
                        continue

                    gw2guild = gw2_guild.get_by_server_uuid(session, server.uuid)

                    # Skip if GW2 Guild is not found on server
                    if gw2guild is None or gw2guild.guild_upgrade_channel is None:
                        continue

                    gw2apikey = gw2_api_key.get_by_player_uuid(session, gw2guild.guild_owner_uuid)

                    # Skip if GW2 Owner Api key is not found for server
                    if gw2apikey is None:
                        continue

                    api_session = Api(api_key=gw2apikey.key)

                    # Get already completed upgrades
                    completed_upgrades = await api_session.guild(gw2guild.guild_gw2_id).upgraded()
                    completed_upgrade_ids = [x.id for x in completed_upgrades if x.type is pygw2.core.models.GuildUpgradeType.Unlock]

                    channel = self.__bot.get_channel(int(gw2guild.guild_upgrade_channel))

                    # Continue if channel wasn't found
                    if channel is None:
                        logger.info(f"No guild upgrades channel found for {server.name}.")
                        continue

                    guild_upgrades = gw2_guild_upgrade.get_ongoing_by_guild_uuid(session, gw2guild.uuid)

                    for upgrade in guild_upgrades:

                        if upgrade.gw2_id in completed_upgrade_ids:
                            updated_upgrade = {
                                "name": upgrade.name,
                                "gw2_id": upgrade.id,
                                "gw2_guild_uuid": upgrade.gw2_guild_uuid,
                                "message_id": upgrade.message_id,
                                "completed": True
                            }
                            upgrade = gw2_guild_upgrade.update(session, db_obj=upgrade, obj_in=updated_upgrade)

                        if upgrade.message_id is None:
                            continue

                        embed = nextcord.Embed()
                        embed.set_author(
                            name=f"{gw2guild.name}",
                            url=settings.URL,
                            icon_url=f"https://emblem.werdes.net/emblem/{gw2guild.guild_gw2_id}",
                        )
                        embed.timestamp = datetime.datetime.utcnow()

                        # Channel must not be bloated with messages
                        message = nextcord.utils.find(
                            lambda m: (m.id == int(upgrade.message_id)),
                            await channel.history(limit=100).flatten(),
                        )

                        # Skip if message wasn't found
                        if message is None:
                            continue

                        upgrade_info = await api_session.guild().upgrades(upgrade.gw2_id)

                        upgrade_status = await get_upgrade_status(api_session, gw2guild.guild_gw2_id, int(upgrade_info.id))

                        embed.title = upgrade_info.name
                        embed.description = upgrade_info.description
                        embed.set_thumbnail(upgrade_info.icon)

                        if not upgrade.completed:
                            for k, v in upgrade_status.items():
                                embed.add_field(name=k, value=v)
                        else:
                            embed.add_field(name="Status", value="Completed")

                        await message.edit(embed=embed)

                    logger.info(f"Guild upgrades updated for {guild.name}.")

    @tasks.loop(minutes=30)
    async def update_available_upgrades(self):
        logger.info("Update available upgrades for Guild Wars 2 Guilds")

        with Session() as session:
            gw2guilds = gw2_guild.get_multi(session)
            for gw2guild in gw2guilds:
                logger.info(f"Updating Guild Wars 2 Guild upgrades for {gw2guild.name}")
                gw2apikey = gw2_api_key.get_by_player_uuid(session, gw2guild.guild_owner_uuid)
                api_session = Api(api_key=gw2apikey.key)

                available_upgrades, available_upgrades_ids = await get_available_guild_upgrades(api_session, gw2guild.guild_gw2_id)

                self.upgrades[gw2guild.guild_gw2_id] = (datetime.datetime.now(), available_upgrades, available_upgrades_ids)
                logger.info(f"Upgrades for {gw2guild.name} found.")

    @nextcord.slash_command("gw2", "Guild Wars 2 commands")
    async def gw2(self, ctx: nextcord.Interaction):
        """
        Guild Wars 2 root command

        :param ctx: Context
        :return:
        """
        embed = nextcord.Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        embed.title = "Guild Wars 2 root command, please select proper subcommand: `apikey` `guild`"
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed, ephemeral=True)

    @gw2.subcommand("apikey", "View your API key")
    async def gw2_apikey(self, ctx: nextcord.Interaction):
        """
        Guild Wars 2 APIKEY command root and view key

        :param ctx: Interaction
        :return:
        """
        async with session_lock:
            with Session() as session:
                player = get_create_ctx(ctx, session, player_crud)
                api_key = gw2_api_key.get_by_player_uuid(session, player.uuid)
                embed = nextcord.Embed()

                if api_key is None:
                    embed.title = f"API key not found!"
                    embed.colour = nextcord.Colour.red()
                else:
                    embed.title = f"API key for {ctx.user.name}"
                    embed.description = f"{api_key.key}"
                    embed.colour = nextcord.Colour.purple()
                embed.timestamp = datetime.datetime.utcnow()
                embed.set_author(name=self.__bot.user.name,
                                 url=settings.URL,
                                 icon_url=self.__bot.user.avatar.url)
                await ctx.send(embed=embed, ephemeral=True)

    @gw2_apikey.subcommand("set", "Set API key")
    async def gw2_set_api_key(self, ctx: nextcord.Interaction, api_key: str):
        """
        Set API key for Guild Wars 2
        :param ctx: Interaction
        :param api_key: API key string
        :return:
        """
        async with session_lock:
            with Session() as session:
                player = get_create_ctx(ctx, session, player_crud)
                db_api_key = gw2_api_key.get_by_player_uuid(session, player.uuid)
                embed = nextcord.Embed()

                if db_api_key is None:
                    new_api_key = {"player_uuid": player.uuid, "key": api_key}
                    gw2_api_key.create(session, obj_in=CreateGw2ApiKey(**new_api_key))
                    embed.title = f"API key has been set."
                    embed.colour = nextcord.Colour.green()
                else:
                    update_api_key = {"key": api_key}
                    gw2_api_key.update(session, db_obj=db_api_key, obj_in=UpdateGw2ApiKey(**update_api_key))
                    embed.title = f"API key has been updated."
                    embed.colour = nextcord.Colour.purple()
                embed.timestamp = datetime.datetime.utcnow()
                embed.set_author(name=self.__bot.user.name,
                                 url=settings.URL,
                                 icon_url=self.__bot.user.avatar.url)
                await ctx.send(embed=embed, ephemeral=True)

    @gw2_apikey.subcommand("unset", "Remove API key")
    async def gw2_unset_api_key(self, ctx: nextcord.Interaction):
        """
        Remove API key for Guild Wars 2
        :param ctx: Interaction
        :return:
        """
        async with session_lock:
            with Session() as session:
                player = get_create_ctx(ctx, session, player_crud)
                api_key = gw2_api_key.get_by_player_uuid(session, player.uuid)
                embed = nextcord.Embed()

                if api_key is None:
                    embed.title = f"API key not found!"
                    embed.colour = nextcord.Colour.red()
                else:
                    embed.title = f"API key removed."
                    embed.colour = nextcord.Colour.green()
                    gw2_api_key.remove(session, uuid=api_key.uuid)
                embed.timestamp = datetime.datetime.utcnow()
                embed.set_author(name=self.__bot.user.name,
                                 url=settings.URL,
                                 icon_url=self.__bot.user.avatar.url)
                await ctx.send(embed=embed, ephemeral=True)

    @gw2.subcommand("guild", "Guild Wars 2 Guild Management")
    async def gw2_guild(self, ctx: nextcord.Interaction):
        """
        Guild Wars 2 GUILD root command

        :param ctx: Context
        :return:
        """
        embed = nextcord.Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        embed.title = "Guild Wars 2 GUILD root command"
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed, ephemeral=True)

    @gw2_guild.subcommand("init", "Guild Wars 2 Guild Initialization")
    @commands.has_permissions(administrator=True)
    async def gw2_guild_init(self, ctx: nextcord.Interaction, guild_name: str):
        """
        Guild Wars 2 initialize guild on current server

        :param ctx: Context
        :param guild_name: Guild Wars 2 Guild name
        :return:
        """
        embed = nextcord.Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        embed.timestamp = datetime.datetime.utcnow()
        async with session_lock:
            with Session() as session:
                server = get_create_ctx(ctx, session, server_crud)
                player = get_create_ctx(ctx, session, player_crud)
                player_api_key = gw2_api_key.get_by_player_uuid(session, player.uuid)
                if player_api_key is None:
                    embed.title = "API key needed for guild initialization!"
                    embed.colour = nextcord.Colour.red()
                else:
                    api_session = Api(api_key=player_api_key.key)
                    new_guild = await add_gw2_guild(session, api_session, guild_name, server.uuid, player.uuid)
                    if new_guild is None:
                        embed.title = "Guild initialization failed!"
                        embed.description = f"Guild `{guild_name}` not found!"
                        embed.colour = nextcord.Colour.red()
                    else:
                        embed.title = f"Guild initialized: {new_guild.name}!"
                        embed.colour = nextcord.Colour.green()
                        embed.set_image(url=f"https://emblem.werdes.net/emblem/{new_guild.guild_gw2_id}")

        await ctx.send(embed=embed, ephemeral=True)

    # @gw2_guild.subcommand("upgrades", "Guild Wars 2 Guild Upgrades Management")
    # async def gw2_guild_upgrades(self, ctx: nextcord.Interaction):
    #     """
    #     Guild Wars 2 GUILD UPGRADES root command

    #     :param ctx: Context
    #     :return:
    #     """
    #     embed = nextcord.Embed()
    #     embed.set_author(
    #         name=self.__bot.user.name,
    #         url=settings.URL,
    #         icon_url=self.__bot.user.avatar.url,
    #     )
    #     embed.title = "Guild Wars 2 GUILD UPGRADES root command"
    #     embed.timestamp = datetime.datetime.utcnow()
    #    await ctx.send(embed=embed, ephemeral=True)

    @gw2_guild.subcommand("init_upgrades", "Initialize Guild Upgrades channel")
    @commands.has_permissions(administrator=True)
    async def gw2_guild_init_upgrades(self, ctx: nextcord.Interaction, channel: nextcord.TextChannel = nextcord.SlashOption(
        description="Channel to post Guild Upgrades"
    )):
        embed = nextcord.Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        embed.timestamp = datetime.datetime.utcnow()
        async with session_lock:
            with Session() as session:
                gw2guild = get_server_guild(session, ctx)
                updated_guild = {
                    "name": gw2guild.name,
                    "server_uuid": gw2guild.server_uuid,
                    "guild_gw2_id": gw2guild.guild_gw2_id,
                    "guild_upgrade_channel": str(channel.id)
                }
                gw2guild = gw2_guild.update(session, db_obj=gw2guild, obj_in=UpdateGw2Guild(**updated_guild))
                embed.title = f"Guild upgrades initialized: {gw2guild.name}!"
                embed.colour = nextcord.Colour.green()
                embed.set_image(url=f"https://emblem.werdes.net/emblem/{gw2guild.guild_gw2_id}")

        await ctx.send(embed=embed, ephemeral=True)

    # @gw2_guild_upgrades.subcommand("track", "Track Guild Wars 2 Guild Upgrade")
    @gw2_guild.subcommand("track_upgrade", "Track Guild Wars 2 Guild Upgrade")
    @commands.has_permissions(administrator=True)   # TODO better permissions ?
    async def gw2_guild_upgrades_track(self, ctx: nextcord.Interaction, upgrade: str = nextcord.SlashOption(
        description="Name of the Guild Upgrade",
        autocomplete_callback=available_guild_upgrades
    )):
        embed = nextcord.Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        embed.timestamp = datetime.datetime.utcnow()

        confirmation = nextcord.Embed()
        confirmation.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        confirmation.timestamp = datetime.datetime.utcnow()

        async with session_lock:
            with Session() as session:
                gw2guild = get_server_guild(session, ctx)

                # If Guild is not found, return
                if gw2guild is None:
                    embed.title = "Guild Wars 2 Guild not found!"
                    embed.colour = nextcord.Colour.red()
                    return await ctx.send(embed=embed, ephemeral=True)

                embed.set_author(
                    name=f"{gw2guild.name}",
                    url=settings.URL,
                    icon_url=f"https://emblem.werdes.net/emblem/{gw2guild.guild_gw2_id}",
                )

                if gw2guild.guild_upgrade_channel is None:
                    embed.title = "Guild Upgrades channel not initialized!"
                    embed.colour = nextcord.Colour.red()
                    return await ctx.send(embed=embed, ephemeral=True)

                channel = self.__bot.get_channel(int(gw2guild.guild_upgrade_channel))

                message = await channel.send(embed=embed)

                fetched_upgrades = self.upgrades.get(gw2guild.guild_gw2_id)

                if fetched_upgrades is not None:
                    try:
                        upgrade_index = fetched_upgrades[1].index(upgrade)
                    except ValueError:
                        upgrade_index = None
                else:
                    upgrade_index = None

                if upgrade_index is not None:
                    upgrade_id = fetched_upgrades[2][upgrade_index]
                    api_session = get_server_api_session(session, ctx)

                    upgrade_info = await api_session.guild().upgrades(upgrade_id)

                    new_upgrade = {
                        "name": upgrade_info.name,
                        "gw2_id": upgrade_info.id,
                        "gw2_guild_uuid": gw2guild.uuid,
                        "message_id": str(message.id)
                    }

                    gw2_guild_upgrade.create(session, obj_in=CreateGw2GuildUpgrade(**new_upgrade))

                    upgrade_status = await get_upgrade_status(api_session, gw2guild.guild_gw2_id, int(upgrade_info.id))

                    embed.title = upgrade_info.name
                    embed.description = upgrade_info.description
                    embed.set_thumbnail(upgrade_info.icon)

                    for k, v in upgrade_status.items():
                        embed.add_field(name=k, value=v)

                    await message.edit(embed=embed)

                    confirmation.title = "Upgrade sent to upgrades channel!"
                    confirmation.colour = nextcord.Colour.green()

                else:
                    confirmation.title = "Guild upgrade tracking failed!"
                    confirmation.description = f"Guild upgrade `{upgrade}` not found or upgrades not loaded!"
                    confirmation.colour = nextcord.Colour.red()

        await ctx.send(embed=confirmation, ephemeral=True)

    @gw2.subcommand("daily", "Interact with Guild Wars 2 Dailies")
    async def gw2_daily(self, ctx: nextcord.Interaction):
        embed = nextcord.Embed()
        embed.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        embed.title = "Guild Wars 2 DAILY root command"
        embed.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=embed, ephemeral=True)

    @gw2_daily.subcommand("get", "Get GW2 Dailies")
    async def gw2_daily_get(self, ctx: nextcord.Interaction, category: str = nextcord.SlashOption(
        description="Daily category",
        choices=["PvE", "PvP", "WvW", "Fractals", "Strikes", "Living World"]
    )):
        if category == "PvP":
            cat = DailyType.PvP
        elif category == "WvW":
            cat = DailyType.WvW
        elif category == "Fractals":
            cat = DailyType.Fractals
        elif category == "Strikes":
            cat = DailyType.Strikes
        elif category == "Living World":
            cat = DailyType.LivingWorld
        else:
            cat = DailyType.PvE

        api_session = Api()

        embed = nextcord.Embed()
        embed.set_author(
            name="Guild Wars 2 Dailies",
            url=settings.URL,
            icon_url="https://wiki.guildwars2.com/images/1/14/Daily_Achievement.png"
        )
        embed.timestamp = datetime.datetime.utcnow()

        icon_url = None

        if cat == DailyType.PvE or cat == DailyType.PvP or cat == DailyType.WvW or cat == DailyType.Fractals:
            root_dailies = api_session.achievements.daily()
            await ctx.response.defer()

            root_dailies = await root_dailies

            if cat == DailyType.PvE:
                dailies = root_dailies.pve
                title = "Daily PvE Achievements"
            elif cat == DailyType.PvP:
                dailies = root_dailies.pvp
                title = "Daily PvP Achievements"
            elif cat == DailyType.WvW:
                dailies = root_dailies.wvw
                title = "Daily WvW Achievements"
            elif cat == DailyType.Fractals:
                dailies = root_dailies.fractals
                title = "Daily Fractal Achievements"
            else:
                title = "Unknown"
                dailies = []

            if len(dailies) > 0:
                icon_url = dailies[-1].achievement.icon

            embed.title = title

            description = ""
            for d in dailies:
                description += f"{d.achievement.name}\n"

            embed.description = description

        elif cat == DailyType.Strikes:
            strikes = await api_session.achievements.categories(250)
            embed.title = "Daily Priority Strikes"
            icon_url = strikes.icon

            description = ""
            for d in strikes.achievements:
                description += f"{d.name}\n"

            embed.description = description

        elif cat == DailyType.LivingWorld:
            lws = await api_session.achievements.categories(238, 243, 330, 321)
            embed.title = "Daily Living World"
            icons = [x.icon for x in lws if x.icon is not None]

            icon_url = random.choice(icons)

            description = ""

            for c in lws:
                description += f"**{c.name}**\n"
                for d in c.achievements:
                    description += f"{d.name}\n"
                description += "\n"

            embed.description = description

        if icon_url is None:
            icon_url = "https://wiki.guildwars2.com/images/1/14/Daily_Achievement.png"

        embed.set_thumbnail(icon_url)

        await ctx.send(embed=embed)

    @gw2_daily.subcommand("subscribe", "Subscribe to GW2 daily updates")
    @commands.has_permissions(administrator=True)
    async def gw2_daily_subscribe(self, ctx: nextcord.Interaction, channel: nextcord.TextChannel = nextcord.SlashOption(
        description="Channel to post daily messages"
    ), category: str = nextcord.SlashOption(
        description="Daily category",
        choices=["PvE", "PvP", "WvW", "Fractals", "Strikes", "Living World"]
    )):
        if category == "PvP":
            cat = DailyType.PvP
        elif category == "WvW":
            cat = DailyType.WvW
        elif category == "Fractals":
            cat = DailyType.Fractals
        elif category == "Strikes":
            cat = DailyType.Strikes
        elif category == "Living World":
            cat = DailyType.LivingWorld
        else:
            cat = DailyType.PvE

        confirmation = nextcord.Embed()
        confirmation.set_author(
            name=self.__bot.user.name,
            url=settings.URL,
            icon_url=self.__bot.user.avatar.url,
        )
        confirmation.timestamp = datetime.datetime.utcnow()

        async with session_lock:
            with Session() as session:
                server = get_create_ctx(ctx, session, server_crud)
                current_sub = gw2_daily_sub.get_by_category(session, server.uuid, cat)

                if current_sub is not None:
                    confirmation.title = "Subscription for this server already exists!"
                    confirmation.colour = nextcord.Colour.red()
                    return await ctx.send(embed=confirmation, ephemeral=True)

                api_session = Api()

                embed = nextcord.Embed()
                embed.set_author(
                    name="Guild Wars 2 Dailies",
                    url=settings.URL,
                    icon_url="https://wiki.guildwars2.com/images/1/14/Daily_Achievement.png"
                )
                embed.timestamp = datetime.datetime.utcnow()

                icon_url = None

                if cat == DailyType.PvE or cat == DailyType.PvP or cat == DailyType.WvW or cat == DailyType.Fractals:
                    root_dailies = api_session.achievements.daily()
                    await ctx.response.defer()

                    root_dailies = await root_dailies

                    if cat == DailyType.PvE:
                        dailies = root_dailies.pve
                        title = "Daily PvE Achievements"
                    elif cat == DailyType.PvP:
                        dailies = root_dailies.pvp
                        title = "Daily PvP Achievements"
                    elif cat == DailyType.WvW:
                        dailies = root_dailies.wvw
                        title = "Daily WvW Achievements"
                    elif cat == DailyType.Fractals:
                        dailies = root_dailies.fractals
                        title = "Daily Fractal Achievements"
                    else:
                        title = "Unknown"
                        dailies = []

                    if len(dailies) > 0:
                        icon_url = dailies[-1].achievement.icon

                    embed.title = title

                    description = ""
                    for d in dailies:
                        description += f"{d.achievement.name}\n"

                    embed.description = description

                elif cat == DailyType.Strikes:
                    strikes = await api_session.achievements.categories(250)
                    embed.title = "Daily Priority Strikes"
                    icon_url = strikes.icon

                    description = ""
                    for d in strikes.achievements:
                        description += f"{d.name}\n"

                    embed.description = description

                elif cat == DailyType.LivingWorld:
                    lws = await api_session.achievements.categories(238, 243, 330, 321)
                    embed.title = "Daily Living World"
                    icons = [x.icon for x in lws if x.icon is not None]

                    icon_url = random.choice(icons)

                    description = ""

                    for c in lws:
                        description += f"**{c.name}**\n"
                        for d in c.achievements:
                            description += f"{d.name}\n"
                        description += "\n"

                    embed.description = description

                if icon_url is None:
                    icon_url = "https://wiki.guildwars2.com/images/1/14/Daily_Achievement.png"

                embed.set_thumbnail(icon_url)

                message = await channel.send(embed=embed)

                new_sub = {
                    "server_uuid": server.uuid,
                    "channel_id": str(channel.id),
                    "message_id": str(message.id),
                    "daily_type": cat,
                }

                gw2_daily_sub.create(session, obj_in=CreateGw2DailySub(**new_sub))

        confirmation.title = f"Subscription for daily {category} created!"
        confirmation.colour = nextcord.Colour.green()
        return await ctx.send(embed=confirmation, ephemeral=True)
