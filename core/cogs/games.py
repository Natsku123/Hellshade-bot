from nextcord.ext import commands, tasks
import asyncio
import time
import datetime
import random
import nextcord
import requests
import re
from aiohttp import ClientSession
from pathlib import Path

from core.config import settings, logger

from core.database import session_lock, Session
from core.database.models.steamnews import Post, Subscription
from core.database.crud.steamnews import post as crud_post, subscription as crud_subscription
from core.database.schemas.steamnews import CreateSubscription, CreatePost


class Games(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot

        self.__heroes = []

        self.update_heroes.start()
        self.patch_notes.start()
        self.get_steam_news.start()

    @tasks.loop(hours=24)
    async def update_heroes(self):
        await self.__bot.wait_until_ready()
        logger.info("Fetching Dota 2 heroes...")

        r = requests.get(
            "https://www.dota2.com/datafeed/herolist?language=english"
        )
        data = r.json()
        if 'result' not in data or \
                'data' not in data['result'] or \
                'heroes' not in data['result']['data']:
            logger.warning("Could not fetch heroes :/")
            return

        heroes = data['result']['data']['heroes']

        self.__heroes = []

        for hero in heroes:
            self.__heroes.append({
                "name": hero['name_loc'],
                "link": f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{hero['name'].removeprefix('npc_dota_hero_')}.png"
            })

        logger.info("Done fetching heroes.")

    @tasks.loop(minutes=30)
    async def get_steam_news(self):
        await self.__bot.wait_until_ready()
        logger.info("Fetching Steam news...")
        async with session_lock:
            with Session() as session:
                subs = crud_subscription.get_multi(session)
                all_new_posts = []
                async with ClientSession() as client:
                    for s in subs:
                        logger.info(
                            f"Fetching news: {s.channel_id=} {s.app_id=}"
                        )
                        async with client.get(f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid={s.app_id}&count=100&maxlength=1500&format=json") as r:
                            if r.status >= 400:
                                logger.warning(
                                    f"Could not find news for app {s.app_id}!"
                                )
                                continue

                            data = await r.json()

                            if 'appnews' not in data or 'newsitems' not in data['appnews']:
                                logger.warning(
                                    f"Could not find news for app {s.app_id}!"
                                )
                                continue

                            new_posts = []

                            for p in data['appnews']['newsitems']:
                                if p['feed_type'] != 1:
                                    continue

                                db_post = crud_post.get_by_gid(session, p['gid'])

                                if db_post is not None:
                                    continue

                                new_posts.append(p)

                            for p in new_posts:
                                all_new_posts.append(p)

                                embed = nextcord.Embed()

                                embed.set_author(
                                    name=f"Steam News - {p['author']}",
                                    icon_url="https://logos-world.net/wp-content/uploads/2020/10/Steam-Logo.png"
                                )
                                embed.title = p['title']
                                embed.url = p['url']
                                desc = re.sub(r"\{\S*\}\/\S*", "\n", p['contents'])
                                embed.description = desc

                                channel = self.__bot.get_channel(
                                    int(s.channel_id)
                                )

                                await channel.send(embed=embed)
                                await asyncio.sleep(0.5)

                # Add all new posts to database so they wont be sent again
                for p in all_new_posts:
                    old_p = crud_post.get_by_gid(session, p['gid'])

                    # Skip if already added
                    if old_p is not None:
                        continue

                    crud_post.create(session, obj_in=CreatePost(**{
                        'steam_gid': p['gid'],
                        'title': p['title'],
                        'content': p['contents']
                    }))

        logger.info("Done fetching Steam news.")

    @tasks.loop(minutes=30)
    async def patch_notes(self):
        await self.__bot.wait_until_ready()
        logger.info("Fetching Dota 2 patch notes...")

        r = requests.get(
            "https://www.dota2.com/datafeed/patchnoteslist?language=english"
        )
        data = r.json()
        if 'patches' not in data:
            logger.warning("Could not fetch patch notes :/")
            return

        latest = data['patches'][-1]['patch_name']

        patch_file = Path('/files/last_title')

        if patch_file.exists():
            with open('/files/last_title', 'r') as pfr:
                last_title = pfr.read()
        else:
            last_title = ""

        if latest > last_title:
            logger.info("New patch notes found!")
            with open('/files/last_title', 'w') as pfw:
                pfw.write(latest)

            embed = nextcord.Embed()

            embed.set_author(name="Dota2.com", icon_url="https://1000logos.net/wp-content/uploads/2019/03/Dota-2-Logo.png")
            embed.title = f"New patch **{latest}** found!"
            embed.url = f"https://www.dota2.com/patches/{latest}"

            # Send messages to configured channel
            # TODO make dynamic
            channel = self.__bot.get_channel(367057131750293514)
            await channel.send(embed=embed)

        logger.info("Done fetching Dota 2 patch notes.")

    @commands.group(no_pm=True)
    async def steam(self, ctx):
        """
        Steam related commands, more on !help steam

        :param ctx: Context
        :return:
        """
        if ctx.invoked_subcommand is None:
            embed = nextcord.Embed()
            embed.set_author(
                name=self.__bot.user.name, url=settings.URL,
                icon_url=self.__bot.user.avatar.url
            )
            embed.title = "Invalid steam command! `!help steam` for more info"
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed)

    @steam.group(name="news", no_pm=True)
    async def steam_news(self, ctx):
        """
        Steam News commands, more on !help steam news

        :param ctx: Context
        :return:
        """
        if ctx.invoked_subcommand is None:
            embed = nextcord.Embed()
            embed.set_author(
                name=self.__bot.user.name, url=settings.URL,
                icon_url=self.__bot.user.avatar.url
            )
            embed.title = "Invalid steam news command! `!help steam news` for more info"
            embed.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=embed)

    @steam_news.command(name="subscribe", pass_context=True, no_pm=True, aliases=['sub'])
    @commands.has_permissions(administrator=True)
    async def steam_news_subscribe(self, ctx, app_id: int):
        """
        Subscribe to Steam News with App ID.

        :param ctx: Context
        :param app_id: ID of a Steam App (can be found in Steam)
        :return:
        """
        async with session_lock:
            with Session() as session:
                sub = crud_subscription.create(session, obj_in=CreateSubscription(**{
                    'channel_id': str(ctx.message.channel.id),
                    'app_id': app_id
                }))
                embed = nextcord.Embed()
                embed.set_author(name=self.__bot.user.name,
                                 url=settings.URL,
                                 icon_url=self.__bot.user.avatar.url)
                embed.title = f"Channel **{ctx.message.channel}** subscribed to Steam App **{sub.app_id}**!"
                embed.timestamp = datetime.datetime.utcnow()
                await ctx.send(embed=embed)

    @steam_news.command(name="clear", pass_context=True, no_pm=True)
    @commands.has_permissions(administrator=True)
    async def steam_news_clear(self, ctx):
        """
        Clear channels subscriptions.

        :param ctx: Context
        :return:
        """
        async with session_lock:
            with Session() as session:
                apps = []
                subs = crud_subscription.get_multi_by_channel_id(session, ctx.message.channel.id)
                for s in subs:
                    old_s = crud_subscription.remove(session, uuid=s.uuid)
                    apps.append(old_s.app_id)

                embed = nextcord.Embed()
                embed.set_author(name=self.__bot.user.name,
                                 url=settings.URL,
                                 icon_url=self.__bot.user.avatar.url)
                embed.title = f"Cleared subscriptions on **{ctx.message.channel}**."
                embed.description = "Removed subscriptions for Steam Apps with IDs:"

                for a in apps:
                    embed.description += f"\n{a}"

                embed.timestamp = datetime.datetime.utcnow()
                await ctx.send(embed=embed)

    @commands.command(pass_context=True)
    async def dota_random(self, ctx):
        index = random.randint(0, len(self.__heroes))
        hero = self.__heroes[index]
        hero_name = hero['name']
        hero_image = hero['link']

        embed = nextcord.Embed()
        embed.title = "You randomed..."
        embed.description = f"Congratulations! You have randomed **{hero_name}**!"
        embed.timestamp = datetime.datetime.utcnow()
        embed.colour = 8161513
        embed.set_author(name=self.__bot.user.name,
                         url=settings.URL,
                         icon_url=self.__bot.user.avatar.url)
        embed.set_image(url=hero_image)
        await ctx.send(embed=embed)

    @commands.command(pass_context=True, hidden=True, no_pm=True)
    async def play_game(self, ctx, game, players, timeout=-1, delay=0.0, roles="noroles"):
        """Search for players. (To be replaced)"""
        if roles != "noroles":
            roles = roles.split(":")
            squad = {str(ctx.message.author): roles[0]}
        else:
            squad = {str(ctx.message.author): ""}
        try:
                i = 0
                mention = ctx.mention
                players = int(players)

                if timeout == -1:
                    timeout = 24*60*60.0
                    delay = 0.0

                else:
                    try:
                        if type(timeout) == str:
                            if "h" not in timeout and "min" not in timeout and "s" not in timeout:
                                timeout = float(timeout)
                            else:
                                raise ValueError
                    except ValueError:
                        try:
                            timeout = str(timeout)
                            if "h" in timeout and "min" in timeout and "s" in timeout:
                                timeout = timeout.split(":")
                                if len(timeout) == 3:
                                    timeout[0] = float(timeout[0].strip("h"))
                                    timeout[1] = float(timeout[1].strip("min"))
                                    timeout[2] = float(timeout[2].strip("s"))
                                    timeout = timeout[0] * 60 * 60 + timeout[
                                        1] * 60 + timeout[2]
                            elif "h" in timeout and "min" in timeout and "s" not in timeout:
                                timeout = timeout.split(":")
                                if len(timeout) == 2:
                                    timeout[0] = float(timeout[0].strip("h"))
                                    timeout[1] = float(timeout[1].strip("min"))
                                    timeout = timeout[0] * 60 * 60 + timeout[
                                        1] * 60
                            elif "h" in timeout and "s" in timeout and "min" not in timeout:
                                timeout = timeout.split(":")
                                if len(timeout) == 2:
                                    timeout[0] = float(timeout[0].strip("h"))
                                    timeout[1] = float(timeout[1].strip("s"))
                                    timeout = timeout[0] * 60 * 60 + timeout[1]
                            elif "min" in timeout and "s" in timeout and "h" not in timeout:
                                timeout = timeout.split(":")
                                if len(timeout) == 2:
                                    timeout[0] = float(timeout[0].strip("min"))
                                    timeout[1] = float(timeout[1].strip("s"))
                                    timeout = timeout[0] * 60 + timeout[1]
                            elif "h" in timeout and "min" not in timeout and "s" not in timeout:
                                timeout = timeout.strip("h")
                                timeout = float(timeout) * 60 * 60
                            elif "min" in timeout and "h" not in timeout and "s" not in timeout:
                                timeout = timeout.strip("min")
                                timeout = float(timeout) * 60
                            elif "s" in timeout and "h" not in timeout and "min" not in timeout:
                                timeout = float(timeout.strip("s"))
                            else:
                                raise ValueError
                        except ValueError:
                            await ctx.send("Invalid timeout value.")
                if delay > 0:
                    await ctx.send("Invitation added to queue.")

                for role in ctx.message.author.roles:
                    if role.name == "-":
                        await ctx.send("Error!")
                        return

                await asyncio.sleep(delay)
                if roles != "noroles":
                    role_text = "Roles: "
                    for role in roles:
                        if role != roles[len(roles)-1]:
                            role_text += role + ", "
                        else:
                            role_text += role
                else:
                    role_text = ""
                await ctx.send("{:}\n**{:}** is inviting players to play **{:}** with **{:}** other players.\nType 'join' if you are interested.{:}".format(mention, ctx.message.author, game, players, role_text))

                try:
                    while i < players:
                        start_time = time.time()

                        def check(m):
                            return m.content.startswith("join")

                        message = await self.__bot.wait_for_message(timeout=timeout,
                                                             channel=ctx,
                                                             check=check)
                        receive_time = time.time()
                        timeout = abs(timeout - (receive_time - start_time))
                        if message is not None and str(message.author) not in squad.keys():
                            i += 1
                            await ctx.send("**{:}** joined squad.\n{:} players needed.".format(message.author, players - i))
                            if len(message.content.split(" ")) > 1:
                                squad[str(message.author)] = message.content.strip("join ")
                            else:
                                squad[str(message.author)] = ""
                            squad_text = ""
                            for player, value in squad.items():
                                if player == list(squad.keys())[len(squad.keys())-1]:
                                    lnb = ""
                                else:
                                    lnb = "\n"
                                if value == "":
                                    squad_text += str(player) + lnb
                                else:
                                    squad_text += str(player) + "(" + str(value) + ")" + lnb
                            await ctx.send("Squad status: ``` {0} ```".format(
                                                              squad_text))

                        elif message is not None and str(message.author) in squad.keys():
                            await ctx.send("You are already in the squad!")
                            squad_text = ""
                            for player, value in squad.items():
                                if player == list(squad.keys())[len(squad.keys()) - 1]:
                                    lnb = ""
                                else:
                                    lnb = "\n"
                                if value == "":
                                    squad_text += str(player) + lnb
                                else:
                                    squad_text += str(player) + "(" + str(
                                        value) + ")" + lnb
                            await ctx.send("Squad status: ``` {0} ```".format(squad_text))
                        elif message is None:
                            break

                        await asyncio.sleep(0.1)
                except Exception as e:
                    logger.exception(e)

                if len(squad) == players + 1:
                    mention_msg = ctx.message.author.mention
                    await ctx.send("Squad ready!\n{:}".format(mention_msg))
                    squad_text = ""
                    for player, value in squad.items():
                        if player == list(squad.keys())[len(squad.keys()) - 1]:
                            lnb = ""
                        else:
                            lnb = "\n"
                        if value == "":
                            squad_text += str(player) + lnb
                        else:
                            squad_text += str(player) + "(" + str(
                                value) + ")" + lnb
                    await ctx.send("Squad status: ``` {0} ```".format(squad_text))
                else:
                    squad_text = ""
                    for player, value in squad.items():
                        if player == list(squad.keys())[len(squad.keys()) - 1]:
                            lnb = ""
                        else:
                            lnb = "\n"
                        if value == "":
                            squad_text += str(player) + lnb
                        else:
                            squad_text += str(player) + "(" + str(
                                value) + ")" + lnb
                    await ctx.send("Times up! Squad status: ``` {0} ```".format(squad_text))
        except ValueError:
            await ctx.send("Number of players must be int! Not " + type(players))

