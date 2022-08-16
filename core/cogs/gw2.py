from pygw2.api import Api

import nextcord
import datetime
from nextcord.ext import commands, tasks

from core.config import settings, logger
from core.database import Session, session_lock
from core.database.crud.gw2_api_key import gw2_api_key
from core.database.crud.gw2_guild import gw2_guild
from core.database.crud.gw2_guild_upgrade import gw2_guild_upgrade
from core.database.crud.players import player as player_crud
from core.database.schemas.gw2_api_key import CreateGw2ApiKey, UpdateGw2ApiKey
from core.database.utils import get_create_ctx


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
