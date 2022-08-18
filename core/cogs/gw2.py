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
from core.database.crud.players import player as player_crud
from core.database.crud.servers import server as server_crud
from core.database.models.gw2_guild import Gw2Guild
from core.database.schemas.gw2_api_key import CreateGw2ApiKey, UpdateGw2ApiKey
from core.database.schemas.gw2_guild import CreateGw2Guild, UpdateGw2Guild
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


async def get_available_guild_upgrades(api_session: Api, guild_id: str) -> list[str]:
    """
    Get available guild upgrades for given guild with given api session

    :param api_session: GW2 API session
    :param guild_id: GW2 Guild ID
    :return: List of upgrade names
    """

    # Get all available upgrades
    all_upgrades = numpy.array(await api_session.guild().upgrades())

    # Get already completed upgrades
    completed_upgrades = await api_session.guild(guild_id).upgraded()
    completed_upgrade_ids = [x.id for x in completed_upgrades if x.type is pygw2.core.models.GuildUpgradeType.Unlock]

    # Match all available upgrades
    available_upgrade_ids = list(all_upgrades[~numpy.isin(all_upgrades, completed_upgrade_ids)])
    available_upgrades = await api_session.guild().upgrades(*available_upgrade_ids)
    available_upgrades = numpy.array([x for x in available_upgrades if x.type is pygw2.core.models.GuildUpgradeType.Unlock])
    prerequisites_done = []

    # Filter upgrades to those that have prerequisites completed
    for x in available_upgrades:
        prerequisites = x.prerequisites
        if not isinstance(prerequisites, list):
            prerequisites = [prerequisites.id]

        else:
            prerequisites = [x.id for x in prerequisites]

        prerequisites_done.append(numpy.all(numpy.isin(prerequisites, completed_upgrade_ids)))

    # Return names of the upgrades
    return [x.name for x in available_upgrades[prerequisites_done]]


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

            available_upgrades = await get_available_guild_upgrades(api_session, gw2guild.guild_gw2_id)

            state.upgrades[gw2guild.guild_gw2_id] = (datetime.datetime.now(), available_upgrades)

        if data != "":
            result = list(filter(lambda x: data.lower() in x.lower(), available_upgrades))
        else:
            result = available_upgrades

        if len(result) > 25:
            result = result[:25]

        return result


class Gw2(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.__bot = bot
        self.upgrades: dict[str, tuple[datetime.datetime, list[str]]] = {}

        self.update_available_upgrades.start()

    @tasks.loop(minutes=30)
    async def upgrade_update(self):
        # TODO
        pass

    @tasks.loop(minutes=30)
    async def update_available_upgrades(self):
        await self.__bot.wait_until_ready()
        logger.info("Update available upgrades for Guild Wars 2 Guilds")

        with Session() as session:
            gw2guilds = gw2_guild.get_multi(session)
            for gw2guild in gw2guilds:
                logger.info(f"Updating Guild Wars 2 Guild upgrades for {gw2guild.name}")
                gw2apikey = gw2_api_key.get_by_player_uuid(session, gw2guild.guild_owner_uuid)
                api_session = Api(api_key=gw2apikey.key)

                available_upgrades = await get_available_guild_upgrades(api_session, gw2guild.guild_gw2_id)

                self.upgrades[gw2guild.guild_gw2_id] = (datetime.datetime.now(), available_upgrades)
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

    # @gw2_guild_upgrades.subcommand("track", "Track Guild Wars 2 Guild Upgrade")
    @gw2_guild.subcommand("track_upgrade", "Track Guild Wars 2 Guild Upgrade")
    async def gw2_guild_upgrades_track(self, ctx: nextcord.Interaction, upgrade: str = nextcord.SlashOption(
        description="Name of the Guild Upgrade",
        autocomplete_callback=available_guild_upgrades
    )):
        pass
