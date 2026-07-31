import asyncio
import datetime
from types import SimpleNamespace

import nextcord

from core.utils import get_admins, gets_exp, level_exp, next_weekday, process_exp, progress_bar


class _FakeBot:
    def __init__(self, team_members):
        self._team_members = team_members

    async def application_info(self):
        return SimpleNamespace(team=SimpleNamespace(members=self._team_members))


def test_get_admins_returns_only_accepted_team_members():
    accepted = nextcord.TeamMembershipState.accepted
    invited = nextcord.TeamMembershipState.invited

    members = [
        SimpleNamespace(id=101, membership_state=accepted),
        SimpleNamespace(id=202, membership_state=invited),
        SimpleNamespace(id=303, membership_state=accepted),
    ]

    admins = asyncio.run(get_admins(_FakeBot(members)))

    assert admins == [101, 303]


def test_gets_exp_true_when_member_is_active_in_non_solo_voice():
    member = SimpleNamespace(
        status=nextcord.Status.online,
        voice=SimpleNamespace(
            channel=SimpleNamespace(members=["a", "b"]),
            self_deaf=False,
            afk=False,
        ),
    )

    assert gets_exp(member) is True


def test_gets_exp_false_for_offline_or_invalid_voice_states():
    offline_member = SimpleNamespace(
        status=nextcord.Status.offline,
        voice=SimpleNamespace(
            channel=SimpleNamespace(members=["a", "b"]),
            self_deaf=False,
            afk=False,
        ),
    )
    solo_member = SimpleNamespace(
        status=nextcord.Status.online,
        voice=SimpleNamespace(
            channel=SimpleNamespace(members=["a"]),
            self_deaf=False,
            afk=False,
        ),
    )
    deaf_member = SimpleNamespace(
        status=nextcord.Status.online,
        voice=SimpleNamespace(
            channel=SimpleNamespace(members=["a", "b"]),
            self_deaf=True,
            afk=False,
        ),
    )
    missing_voice_member = SimpleNamespace(status=nextcord.Status.online, voice=None)

    assert gets_exp(offline_member) is False
    assert gets_exp(solo_member) is False
    assert gets_exp(deaf_member) is False
    assert gets_exp(missing_voice_member) is False


def test_progress_bar_uses_expected_fill_and_empty_segments():
    bar = progress_bar(current=50, goal=100, multiplier=100, divider=10)

    assert bar == "[=====.....]"


def test_level_exp_matches_formula_transitions():
    assert level_exp(1) == 1000
    assert level_exp(2) == 1002
    assert level_exp(90) == 10506
    assert level_exp(91) == 10715
    assert level_exp(100) == 11189


def test_next_weekday_returns_next_occurrence_not_same_day():
    monday = datetime.datetime(2026, 7, 27, 12, 0, 0)  # Monday

    next_monday = next_weekday(monday, 0)
    next_friday = next_weekday(monday, 4)

    assert next_monday == datetime.datetime(2026, 8, 3, 12, 0, 0)
    assert next_friday == datetime.datetime(2026, 7, 31, 12, 0, 0)


def test_process_exp_applies_multiple_level_ups_and_remainder():
    # Level 0 -> 1 requires 1000, level 1 -> 2 requires 1002.
    level, remaining_exp = process_exp(current_level=0, exp=2505)

    assert level == 2
    assert remaining_exp == 503
