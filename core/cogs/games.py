from discord.ext import commands, tasks
import asyncio
import time
import datetime
import random
import discord
from pathlib import Path

from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


from core.config import settings, logger


selenium_exec = ThreadPoolExecutor(2)

loop = asyncio.get_event_loop()


def get_heroes():
    final = []

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
        final.append({
            "name": hero,
            "link": links[i]
        })

    driver.quit()

    return final


def get_news_update():
    lines = []

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(
        options=chrome_options
    )
    driver.get("https://www.dota2.com/news/updates")

    content = WebDriverWait(driver, 10).until(
        EC.visibility_of_all_elements_located((
            By.XPATH,
            ".//div[starts-with(@class, 'updatecapsule_UpdateCapsule_')]"
        )))

    if len(content) > 0:
        content = content[0]

    try:
        date = content.find_element_by_xpath(
            ".//div[starts-with(@class, 'updatecapsule_Date_')]").get_attribute(
            'innerHTML')
        date = datetime.datetime.strptime(date, "%B %d, %Y")

        date_file = Path('/files/last_news')

        if date_file.exists():
            with open('/files/last_news', "r") as t_file:
                last_date = datetime.datetime.fromisoformat(t_file.read())
        else:
            last_date = ""

        if last_date == "" or date > last_date:
            logger.info("New news article found!")

            with open('/files/last_news', "w") as t_file:
                t_file.write(date.isoformat())

            title = content.find_element_by_xpath(
                ".//div[starts-with(@class, 'updatecapsule_Title_')]").get_attribute(
                'innerHTML')

            desc = content.find_element_by_xpath(
                ".//div[starts-with(@class, 'updatecapsule_Desc_')]").text

            lines.append(f"__New update article__: __**{title}**__\n")
            lines.append(f"Released: __{date.date().isoformat()}__\n\n")
            for i in desc.split("\n"):
                lines.append(f" - {i}\n")

    except NoSuchElementException:
        driver.quit()
        return []

    driver.quit()

    return lines


def get_patchnotes():
    lines = []

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(
        options=chrome_options
    )
    driver.get("http://www.dota2.com/patches/")

    content = WebDriverWait(driver, 10).until(
        EC.visibility_of_all_elements_located((
            By.ID, "dota_react_root"
        )))

    if len(content) > 0:
        content = content[0]

    title = content.find_element_by_xpath(
        ".//div[starts-with(@class, 'patchnotespage_NotesTitle_')]").get_attribute(
        'innerHTML')

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

        # Get base elements for each section
        generic_notes = content.find_elements_by_xpath(
            ".//div[starts-with(@class, 'patchnotespage_PatchNoteGeneric_')]"
        )
        item_notes = content.find_elements_by_xpath(
            ".//div[starts-with(@class, 'patchnotespage_PatchNoteItem_')]"
        )
        hero_notes = content.find_elements_by_xpath(
            ".//div[starts-with(@class, 'patchnotespage_PatchNoteHero_')]"
        )

        # Parse generic notes
        parsed_generic_notes = [e.find_element_by_xpath(
            ".//div[starts-with(@class, 'patchnotespage_Note_')]"
        ).get_attribute('innerHTML') for e in generic_notes]

        parsed_item_notes = {}

        # Parse items
        for i in item_notes:
            i_name = i.find_element_by_xpath(
                ".//div[starts-with(@class, 'patchnotespage_ItemName_')]"
            ).get_attribute('innerHTML')
            i_content = i.find_elements_by_xpath(
                ".//div[starts-with(@class, 'patchnotespage_Note_')]"
            )
            parsed_item_notes[i_name] = [
                e.get_attribute('innerHTML') for e in i_content
            ]

        parsed_hero_notes = {}

        # Parse heroes
        for h in hero_notes:
            h_name = h.find_element_by_xpath(
                ".//div[starts-with(@class, 'patchnotespage_HeroName_')]"
            ).get_attribute('innerHTML')
            h_abilities = h.find_elements_by_xpath(
                ".//div[starts-with(@class, 'patchnotespage_AbilityNote_')]"
            )
            h_generic = h.find_elements_by_xpath(
                ".//div[starts-with(@class, 'patchnotespage_Note_')]"
            )

            try:
                h_talents = h.find_element_by_xpath(
                    ".//div[starts-with(@class, 'patchnotespage_TalentNotes_')]"
                ).find_elements_by_xpath(
                    ".//div[starts-with(@class, 'patchnotespage_Note_')]"
                )
            except NoSuchElementException:
                h_talents = []

            h_parsed_generic = [e.get_attribute('innerHTML') for e in
                                h_generic]
            h_parsed_talents = [e.get_attribute('innerHTML') for e in
                                h_talents]

            # Remove duplicates from generic
            for n in h_parsed_talents:
                if n in h_parsed_generic:
                    h_parsed_generic.remove(n)

            h_parsed_abilities = {}

            # Parse abilities
            for a in h_abilities:
                a_name = a.find_element_by_xpath(
                    ".//div[starts-with(@class, 'patchnotespage_AbilityName_')]"
                ).get_attribute('innerHTML')
                a_notes = a.find_elements_by_xpath(
                    ".//div[starts-with(@class, 'patchnotespage_Note_')]"
                )

                h_parsed_abilities[a_name] = [
                    e.get_attribute('innerHTML') for e in a_notes
                ]

                # Remove duplicates from generic
                for n in h_parsed_abilities[a_name]:
                    if n in h_parsed_generic:
                        h_parsed_generic.remove(n)

            parsed_hero_notes[h_name] = {
                "generic": h_parsed_generic,
                "abilities": h_parsed_abilities,
                "talents": h_parsed_talents
            }

        lines = [f"__New Patch:__ __**{title}**__\n"]
        if len(parsed_generic_notes) > 0:
            lines.append("\n__**General**__\n")

            for thing in parsed_generic_notes:
                if thing[-1] == ":":
                    continue
                lines.append(f" - {thing}\n")
            lines.append("\n")

        if len(parsed_item_notes) > 0:
            lines.append("\n__**Items**__")

            for name, notes in parsed_item_notes.items():
                lines.append(f"\n__*{name}*__\n")

                for note in notes:
                    lines.append(f" - {note}\n")
            lines.append("\n")

        if len(parsed_hero_notes) > 0:
            lines.append("\n__**Heroes**__")

            for name, content in parsed_hero_notes.items():
                lines.append(f"\n__*{name}*__\n")

                for note in content['generic']:
                    lines.append(f" - {note}\n")

                for name, notes in content['abilities'].items():
                    lines.append(f"***{name}***\n")

                    for note in notes:
                        lines.append(f" - {note}\n")

                if len(content['talents']) > 0:
                    lines.append("***Talents***\n")

                    for talent in content['talents']:
                        lines.append(f" - {talent}\n")

            lines.append("\n")

    driver.quit()

    return lines


class Games(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot

        self.__heroes = []

        self.update_heroes.start()
        self.patch_notes.start()
        self.news_updates.start()

    @tasks.loop(hours=24)
    async def update_heroes(self):
        await self.__bot.wait_until_ready()
        self.__heroes = await loop.run_in_executor(selenium_exec, get_heroes)

    @tasks.loop(minutes=30)
    async def patch_notes(self):
        await self.__bot.wait_until_ready()
        logger.info("Searching for patch notes...")

        lines = await loop.run_in_executor(selenium_exec, get_patchnotes)

        if len(lines) > 0:
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

    @tasks.loop(minutes=30)
    async def news_updates(self):
        await self.__bot.wait_until_ready()
        logger.info("Searching for news updates...")

        lines = await loop.run_in_executor(selenium_exec, get_news_update)

        if len(lines) > 0:
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

