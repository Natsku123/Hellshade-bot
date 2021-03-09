import math
import datetime
import discord

from typing import Tuple


def get_admins():
    """
    Gets members of Discord Developer Team

    :return:
    """
    admins = []
    for team_member in discord.AppInfo.team.members:
        if team_member.membership_state == \
                discord.TeamMembershipState.accepted:
            admins.append(team_member.id)
    return admins


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
        return math.ceil(1000 + 1.2*(value-1)**2)
    else:
        return math.ceil(1000 + 1024*(value-1)**0.5)


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
