import math
import datetime
import nextcord

from typing import Tuple
from core.config import logger

from enum import Enum


class Colors(int, Enum):
    """
    Color palette
    """
    unauthorized = 16312092
    error = 13632027
    success = 1171983
    other = 8161513


async def get_admins(bot):
    """
    Gets members of Discord Developer Team

    :return:
    """
    admins = []
    info = await bot.application_info()
    for team_member in info.team.members:
        if team_member.membership_state == \
                nextcord.TeamMembershipState.accepted:
            admins.append(team_member.id)
    return admins


def gets_exp(member):
    try:
        return member.status is not nextcord.Status.offline and \
               member.voice is not None and \
               len(member.voice.channel.members) > 1 and \
               member.voice != nextcord.VoiceState.self_deaf and \
               member.voice != nextcord.VoiceState.afk
    except AttributeError:
        return False


def progress_bar(
        current: int, goal: int, multiplier: int = 100, divider: int = 4
) -> str:
    """
    Create a progress bar with
    :param current: current value of bar
    :param goal: goal value of bar
    :param multiplier: bar length multiplier
    :param divider: bar length divider
    :return:
    """
    progress = "=" * int(
        (current / goal * multiplier) // divider
    )
    empty = "." * int(
        ((goal - current) / goal * multiplier) // divider
    )
    return "[" + progress + empty + "]"


def level_exp(value: int) -> int:
    """
    Calculate experience needed to reach level
    :param value:
    :return:
    """
    if value == 1:
        return 1000
    if value < 91:
        return math.ceil(1000 + 1.2 * (value - 1) ** 2)
    else:
        return math.ceil(1000 + 1024 * (value - 1) ** 0.5)


def next_weekday(d: datetime.datetime, weekday: int) -> datetime.datetime:
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)


def process_exp(current_level: int, exp: int) -> Tuple[int, int]:
    """
    Recursively process experience
    :param current_level: Current value of level
    :param exp: Current experience
    :return: new current level, new current experience
    """
    next_level_exp = level_exp(current_level + 1)

    while next_level_exp <= exp:
        exp -= next_level_exp
        current_level += 1
        next_level_exp = level_exp(current_level + 1)

    return current_level, exp
