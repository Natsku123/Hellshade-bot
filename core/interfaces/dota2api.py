from datetime import datetime
from pydantic import BaseModel, AnyHttpUrl
from aiohttp import ClientSession

from core.config import settings, logger
from core.database.models import DotaGuild, Member


class Dota2GuildInfo(BaseModel):
    guild_name: str
    guild_tag: str
    created_timestamp: datetime
    guild_language: int
    guild_flags: int
    guild_logo: str
    guild_region: int
    guild_chat_group_id: str
    guild_description: str
    default_chat_channel_id: str
    guild_primary_color: int
    guild_secondary_color: int
    guild_pattern: int
    guild_refresh_time_offset: int
    guild_required_rank_tier: int
    guild_motd_timestamp: datetime
    guild_motd: str


class Dota2EventPoint(BaseModel):
    event_id: int
    guild_points: int
    guild_weekly_rank: int
    guild_weekly_percentile: int
    guild_current_percentile: int


class Dota2GuildSummary(BaseModel):
    guild_info: Dota2GuildInfo
    member_count: int
    event_points: list[Dota2EventPoint]


class Dota2GuildPersonaInfo(BaseModel):
    guild_id: int
    guild_tag: str
    guild_flags: int


class Dota2Hero(BaseModel):
    id: int
    name: str
    name_loc: str
    primary_attr: int
    complexity: int


async def get_guild_summary(client: ClientSession, guild: DotaGuild) -> Dota2GuildSummary | None:
    """
    Retrieves the guild summary from Dota 2 API
    :param client: Aiohttp Client
    :param guild: Dota Guild
    :return: Dota2GuildSummary
    """
    async with client.get(
            f"https://www.dota2.com/webapi/IDOTA2Guild/GetGuildSummary/v0001/"
            f"?key={settings.STEAM_API_KEY}&guild_id={guild.guild_id}&format=json") as r:
        if r.status >= 400:
            text = await r.text()
            logger.warning(
                f"Could not find Dota Guild {guild.guild_id}! {r.status=} {text=}"
            )
            return None

        data = await r.json()

        if not data["success"] or "summary" not in data:
            logger.warning(f"Could not find Dota Guild {guild.guild_id}! {data=}")
            return None

        return Dota2GuildSummary.parse_obj(data["summary"])


async def get_guild_persona_infos(client: ClientSession, member: Member) -> list[Dota2GuildPersonaInfo]:
    """
    Gets information about guild personas of given member
    :param client: Aiohttp Client
    :param member: Member
    :return: List of Dota 2 Guild Personas
    """
    if member.player.steam_id is None:
        return []

    async with client.get(
            f"https://www.dota2.com/webapi/IDOTA2Guild/GetGuildPersonaInfo/v0001/"
            f"?key={settings.STEAM_API_KEY}&account_id={member.player.steam_id}&format=json") as r:
        if r.status >= 400:
            text = await r.text()
            logger.warning(
                f"Could not find Dota Guild Persona {member.player.name}! {r.status=} {text=}"
            )
            return []

        data = await r.json()

        if not data["success"] or "account_guilds_persona_info" not in data or \
                "guild_persona_infos" not in data["account_guilds_persona_info"]:
            logger.warning(f"Could not find Dota Guild Persona {member.player.name}! {data=}")
            return []

        return [Dota2GuildPersonaInfo.parse_obj(x) for x in data["account_guilds_persona_infos"]["guild_persona_infos"]]


async def get_heroes(client: ClientSession) -> list[Dota2Hero]:
    async with client.get("https://www.dota2.com/datafeed/herolist?language=english") as r:
        if r.status >= 400:
            text = await r.text()
            logger.warning(
                f"Could not find Dota Heroes! {r.status=} {text=}"
            )
            return []

        data = await r.json()

        if 'result' not in data or 'data' not in data["result"] or "heroes" not in data["result"]["data"]:
            logger.warning(f"Could not fetch heroes :/ {data=}")
            return []

        return [Dota2Hero.parse_obj(x) for x in data["result"]["data"]["heroes"]]


def get_guild_icon(icon_id: str) -> AnyHttpUrl:
    # TODO
    return f"https://steamusercontent-a.akamaihd.net/ugc/{icon_id}/BB15623560DDC2B8785B7CCA0701185359F98765/"
