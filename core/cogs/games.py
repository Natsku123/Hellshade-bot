from discord.ext import commands
import asyncio
import time
import datetime
import requests
import bs4
import random
import discord

from core.config import settings


class Games(commands.Cog):
    def __init__(self, bot, logger):
        self.__bot = bot
        self.__logger = logger

        self.__heroes = []
        response = requests.get("http://www.dota2.com/heroes/")
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        heroes = soup.select("#filterName")[0].select("option")
        for hero in heroes:
            if hero.attrs['value'] != "":
                self.__heroes.append({
                    "name": hero.contents[0],
                    "value": hero.attrs['value']
                })

    @commands.command(pass_context=True)
    async def dota_random(self, ctx):
        index = random.randint(0, len(self.__heroes))
        hero = self.__heroes[index]
        hero_name = hero['name']
        hero_image = f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/heroes/{hero['value']}_full.png?v=6120190?v=6120190"

        embed = discord.Embed()
        embed.title = "You randomed..."
        embed.description = f"Congratulation! You have randomed **{hero_name}**!"
        embed.timestamp = datetime.datetime.utcnow()
        embed.colour = 8161513
        embed.set_author(name=self.__bot.user.name,
                         url=settings.URL,
                         icon_url=self.__bot.user.avatar_url)
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
                    self.__logger.exception(e)

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


def setup(bot, logger):
    bot.add_cog(Games(bot, logger))
