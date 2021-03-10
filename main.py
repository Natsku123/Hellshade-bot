from pathlib import Path
import signal
import asyncio
import bs4
import datetime
import discord
import logging
import math
import requests
from discord.ext import commands, tasks

from core.cogs.games import Games
from core.cogs.utility import Utility
from core.config import settings
from core.database import Session, session_lock
from core.database.utils import get_create
from core.database.crud.levels import level as crud_level
from core.database.crud.members import member as crud_member
from core.database.crud.players import player as crud_player
from core.database.crud.servers import server as crud_server
from core.database.schemas.levels import CreateLevel
from core.database.schemas.members import CreateMember
from core.database.schemas.players import CreatePlayer
from core.database.schemas.servers import CreateServer
from core.utils import next_weekday, level_exp


class Shutdown(Exception):
    pass


running = True

cogs = ['core.cogs.utility', 'core.cogs.games']

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler(
#     filename='files/discord.log', encoding='utf-8', mode='w'
# )
handler.setFormatter(
    logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
)
logger.addHandler(handler)


def main():

    logger.info("Starting Bot...")

    description = '''
    Rewrite of the original Hellshade-bot and Hellshade-bot 2
    '''

    # Intents for experience tracking
    intent = discord.Intents.default()
    intent.members = True

    bot = commands.Bot(
        command_prefix=commands.when_mentioned_or('!', '/'),
        description=description,
        owner_id=settings.BOT_OWNER,
        intent=intent
    )

    bot.add_cog(Utility(bot, settings.ADMINS, logger))
    bot.add_cog(Games(bot, logger))

    exp_lock = asyncio.Lock()

    @tasks.loop(hours=168)
    async def weekly_top5():
        await bot.wait_until_ready()
        now = datetime.datetime.now()
        next_sat = next_weekday(now, 5).replace(hour=12, minute=0, second=0)

        delta = next_sat - now
        await asyncio.sleep(delta.total_seconds())
        async with session_lock:
            with Session() as session:
                for server in bot.guilds:
                    server_obj = get_create(
                        session, crud_server, obj_in=CreateServer(**{
                            "discord_id": server.id,
                            "name": server.name,
                            "server_exp": 0,
                            "channel": None
                        })
                    )

                    if server_obj.channel is None:
                        continue

                    top_5 = crud_member.get_top(session, server_obj.uuid, 5)

                    embed = discord.Embed()
                    embed.title = f"Weekly TOP 5 on **{server_obj.name}**"
                    embed.description = f"More data can be found " \
                                        f"[here]({settings.URL}/servers/" \
                                        f"{server_obj.uuid})"
                    embed.url = f"{settings.URL}/servers/{server_obj.uuid}/top5"
                    embed.timestamp = datetime.datetime.utcnow()
                    embed.colour = 8161513
                    embed.set_author(name=bot.user.name,
                                     url=settings.URL,
                                     icon_url=bot.user.avatar_url)

                    for member in top_5:
                        embed.add_field(
                            name=f"**{member.player.name}**",
                            value=f"- LVL: **{member.level.value}** "
                                  f"- EXP: **{member.exp}**",
                            inline=False
                        )

                    await bot.get_channel(int(server_obj.channel)).\
                        send(embed=embed)

    @tasks.loop(minutes=30)
    async def patch_notes():
        await bot.wait_until_ready()
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
            channel = bot.get_channel(367057131750293514)
            for message in new_content:
                await channel.send(message)
                await asyncio.sleep(0.5)

    @tasks.loop(minutes=1)
    async def online_experience():
        await bot.wait_until_ready()
        async with exp_lock:
            async with session_lock:
                with Session() as session:
                    leveled_up = {}
                    for member in bot.get_all_members():
                        if member.status is not discord.Status.offline and \
                                member.voice is not None and \
                                len(member.voice.channel.members) > 1 and \
                                member.voice != discord.VoiceState.self_deaf and \
                                member.voice != discord.VoiceState.afk:
                            player_obj = get_create(
                                session, crud_player, obj_in=CreatePlayer(**{
                                    "discord_id": member.id,
                                    "name": member.name,
                                    "hidden": True
                                })
                            )

                            server_obj = get_create(
                                session, crud_server, obj_in=CreateServer(**{
                                    "discord_id": member.guild.id,
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
                            exp = math.ceil(
                                len(member.voice.channel.members) / 4 * base_exp
                            )

                            if member_obj.level is not None:
                                next_level = crud_level.get_by_value(
                                    session, member.level.value + 1
                                )
                            else:
                                next_level = crud_level.get_by_value(
                                    session, 1
                                )

                            if next_level is None and member_obj.level is not None:
                                member_dict = {
                                    "exp": level_exp(member.level.value+1),
                                    "value": member.level.value+1
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
                                        leveled_up[server_obj.channel].\
                                            append(member_obj)
                                    else:
                                        leveled_up[server_obj.channel]\
                                            = [member_obj]
                            crud_server.update(
                                session, db_obj=server_obj, obj_in={
                                    "name": member.guild.name,
                                    "server_exp": server_obj.server_exp + exp
                                }
                            )

                    for channel in leveled_up:
                        embed = discord.Embed()
                        embed.set_author(name=bot.user.name,
                                         url=settings.URL,
                                         icon_url=bot.user.avatar_url)
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

                        await bot.get_channel(int(channel)).send(embed=embed)

                    logger.info("Experience calculated.")

    @bot.event
    async def on_ready():
        logger.info(f"\nLogged in as:\n{bot.user} (ID: {bot.user.id})")

    @bot.event
    async def on_server_join(server):
        async with session_lock:
            with Session() as session:
                get_create(
                    session, crud_server, obj_in=CreateServer(**{
                        "discord_id": server.id,
                        "name": server.name,
                        "server_exp": 0,
                        "channel": None
                    })
                )

    @bot.event
    async def on_member_join(member):
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
                        "discord_id": member.guild.id,
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

    @bot.event
    async def on_message(message):
        if message.author.id != bot.user.id and not message.author.bot:
            async with session_lock:
                with Session() as session:
                    db_server = get_create(
                        session, crud_server, obj_in=CreateServer(**{
                            "discord_id": message.guild.id,
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
                            session, db_obj=db_member, obj_in={"exp": db_member.exp + 25}
                        )
                    else:
                        db_member = crud_member.update(
                            session, db_obj=db_member, obj_in={
                                "exp": (db_member.exp + 25 - next_level.exp),
                                "level_uuid": next_level.uuid
                            }
                        )
                        if db_member.server.channel is not None:
                            embed = discord.Embed()
                            embed.set_author(name=bot.user.name,
                                             url=settings.URL,
                                             icon_url=bot.user.avatar_url)
                            embed.title = f"**{db_member.player.name}** " \
                                          f"leveled up!"
                            embed.description = f"**{db_member.player.name}" \
                                                f"** leveled up to level " \
                                                f"**{db_member.level.value}" \
                                                f"** by sending messages!"
                            embed.colour = 9942302

                            await bot.get_channel(
                                int(db_member.server.channel)
                            ).send(embed=embed)

        await bot.process_commands(message)

    @bot.event
    async def on_reaction_add(reaction, user):
        if not user.bot:
            async with session_lock:
                with Session() as session:
                    db_server = get_create(
                        session, crud_server, obj_in=CreateServer(**{
                            "discord_id": user.guild.id,
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
                            embed = discord.Embed()
                            embed.set_author(name=bot.user.name,
                                             url=settings.URL,
                                             icon_url=bot.user.avatar_url)
                            embed.title = f"**{db_member.player.name}** " \
                                          f"leveled up!"
                            embed.description = f"**{db_member.player.name}" \
                                                f"** leveled up to level " \
                                                f"**{db_member.level.value}" \
                                                f"** by reacting!"
                            embed.colour = 9942302

                            await bot.get_channel(
                                int(db_member.server.channel)
                            ).send(embed=embed)

    online_experience.start()
    weekly_top5.start()
    patch_notes.start()

    def handle_sigterm(sig, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, handle_sigterm)

    bot.run(settings.BOT_TOKEN)


if __name__ == '__main__':
    main()
