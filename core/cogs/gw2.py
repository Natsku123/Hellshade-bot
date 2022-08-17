import pygw2.core.models
from pygw2.api import Api

import nextcord
import datetime
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


class Gw2(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.__bot = bot

    @tasks.loop(minutes=30)
    async def upgrade_update(self):
        # TODO
        pass

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
