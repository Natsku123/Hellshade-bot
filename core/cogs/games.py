from discord.ext import commands, tasks
import asyncio
import time
import datetime
import requests
import bs4
import random
import discord
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


from core.config import settings, logger


class Games(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot

        self.__heroes = []

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(
            options=chrome_options
        )
        driver.get("http://www.dota2.com/heroes/")

        elements = WebDriverWait(driver, 10).until(
            EC.visibility_of_all_elements_located((
                By.XPATH, "//a[starts-with(@href, '/hero/')]"
            )))

        heroes = [e.find_element_by_xpath(
            ".//div[starts-with(@class, 'herogridpage_HeroName_')]"
        ).get_attribute("innerHTML") for e in elements]

        links = [e.get_attribute('style').split("\"")[1] for e in elements]

        for i, hero in enumerate(heroes):
            self.__heroes.append({
                "name": hero,
                "link": links[i]
            })

        driver.quit()

        self.patch_notes.start()

    @tasks.loop(minutes=30)
    async def patch_notes(self):
        await self.__bot.wait_until_ready()
        logger.info("Searching for patch notes...")
        response = requests.get('http://www.dota2.com/patches/')
        soup = bs4.BeautifulSoup(response.text, "html.parser")

        title = soup.select("p.PatchTitle")[0].text

        title_file = Path('/files/last_title')

        if title_file.exists():
            with open('/files/last_title', "r") as t_file:
                last_title = t_file.read()
        else:
            last_title = ""

        if title > last_title:

            logger.info("New patch notes found!")

            with open('/files/last_title', "w") as t_file:
                t_file.write(title)

            parsed_items = []
            parsed_heroes = []
            parsed_general = []

            general = soup.select("#GeneralSection")
            if len(general) != 0:
                general = general[0].select("li.PatchNote")
                for thing in general:
                    if 'HideDot' not in thing.attrs['class']:
                        parsed_general.append(thing.text.strip())

            items = soup.select("#ItemsSection")
            if len(items) != 0:
                items = items[0]
                for item in items.contents:
                    if item.name == "div":
                        if hasattr(item, "text"):
                            notes = []
                            for note in item.select("li.PatchNote"):
                                if 'HideDot' not in note.attrs['class']:
                                    notes.append(note.text.strip())
                            parsed_items.append({
                                "name": item.select("div.ItemName")[0].text,
                                "notes": notes
                            })

            heroes = soup.select("#HeroesSection")
            if len(heroes) != 0:
                heroes = heroes[0]
                for hero in heroes.contents:
                    if hero.name == "div":
                        logger.info("Name:", hero.select("div.HeroName")[0].text)

                        # Parse Hero notes
                        hero_notes = []
                        hero_note_list = hero.select("ul.HeroNotesList")
                        if len(hero_note_list) > 0:
                            for note in hero_note_list[0].select(
                                    "li.PatchNote"):
                                if 'HideDot' not in note.attrs['class']:
                                    hero_notes.append(note.text.strip())

                        # Parse Ability notes
                        parsed_abilities = []
                        for ability in hero.select("div.HeroAbilityNotes"):
                            ability_notes = []
                            for note in ability.select("li.PatchNote"):
                                if 'HideDot' not in note.attrs['class']:
                                    ability_notes.append(note.text.strip())
                            parsed_abilities.append({
                                "name": ability.select("div.AbilityName")[
                                    0].text,
                                "notes": ability_notes
                            })

                        # Parse Talent notes
                        talent_notes = hero.select("div.TalentNotes")
                        if len(talent_notes) > 0:
                            parsed_talents = []
                            for note in talent_notes[0].select("li.PatchNote"):
                                if 'HideDot' not in note.attrs['class']:
                                    parsed_talents.append(note.text.strip())
                        else:
                            parsed_talents = []

                        # Assemble info of Hero
                        parsed_heroes.append({
                            "name": hero.select("div.HeroName")[0].text,
                            "notes": hero_notes,
                            "abilities": parsed_abilities,
                            "talents": parsed_talents
                        })

            lines = [f"__New Patch:__ __**{title}**__\n"]
            if len(parsed_general) > 0:
                lines.append("\n__**General**__\n")

                for thing in parsed_general:
                    lines.append(f" - {thing}\n")
                lines.append("\n")

            if len(parsed_items) > 0:
                lines.append("\n__**Items**__")

                for item in parsed_items:
                    lines.append(f"\n__*{item['name']}*__\n")

                    for note in item['notes']:
                        lines.append(f" - {note}\n")
                lines.append("\n")

            if len(parsed_heroes) > 0:
                lines.append("\n__**Heroes**__")

                for hero in parsed_heroes:
                    lines.append(f"\n__*{hero['name']}*__\n")

                    for note in hero['notes']:
                        lines.append(f" - {note}\n")

                    for ability in hero['abilities']:
                        lines.append(f"***{ability['name']}***\n")

                        for note in ability['notes']:
                            lines.append(f" - {note}\n")

                    if len(hero['talents']) > 0:
                        lines.append("***Talents***\n")

                        for talent in hero['talents']:
                            lines.append(f" - {talent}\n")

                lines.append("\n")

            new_content = [""]
            for line in lines:
                if len(line) + len(new_content[-1]) >= 2000:
                    new_content.append("")

                new_content[-1] += line

            # Send messages to configured channel
            # TODO make dynamic
            channel = self.__bot.get_channel(367057131750293514)
            for message in new_content:
                await channel.send(message)
                await asyncio.sleep(0.5)

    @commands.command(pass_context=True)
    async def dota_random(self, ctx):
        index = random.randint(0, len(self.__heroes))
        hero = self.__heroes[index]
        hero_name = hero['name']
        hero_image = hero['link']

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

