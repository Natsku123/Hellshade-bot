import asyncio
import os
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_USER"] = "test"
os.environ["DB_PASS"] = "test"
os.environ["DB_NAME"] = "test"

from core.database import Base, engine
from core.cogs.games import Games
from core.cogs.roles import Roles
from core.cogs.utility import Utility


@dataclass
class FakeUser:
    id: int
    name: str
    bot: bool = False
    discriminator: str = "0001"

    def __post_init__(self) -> None:
        self.roles: list[Any] = []

    async def add_roles(self, *roles: Any, **kwargs: Any) -> None:
        self.roles.extend(roles)

    async def remove_roles(self, *roles: Any, **kwargs: Any) -> None:
        for role in roles:
            if role in self.roles:
                self.roles.remove(role)


class FakeMessage:
    def __init__(self, channel: "FakeChannel") -> None:
        self.channel = channel
        self.id = 1000
        self.reactions: list[Any] = []
        self.edited = False

    async def edit(self, *args, **kwargs) -> "FakeMessage":
        self.edited = True
        self.args = args
        self.kwargs = kwargs
        return self

    async def add_reaction(self, emoji: Any) -> None:
        self.reactions.append(emoji)


class FakeChannel:
    def __init__(self, channel_id: int = 42) -> None:
        self.id = channel_id
        self.sent_messages: list[dict[str, Any]] = []
        self.messages: list[FakeMessage] = []

    async def send(self, *args, **kwargs):
        payload = {"args": args, "kwargs": kwargs}
        self.sent_messages.append(payload)
        message = FakeMessage(self)
        self.messages.append(message)
        return message

    def typing(self):
        class _TypingContext:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        return _TypingContext()


class FakeInteraction:
    def __init__(self, *, user: Any = None, guild: Any | None = None, channel: FakeChannel | None = None) -> None:
        self.user = user or FakeUser(id=1, name="tester")
        self.guild = guild or SimpleNamespace(id=999, name="Test Guild")
        self.channel = channel or FakeChannel()
        self.sent_messages: list[dict[str, Any]] = []
        self.invoked_subcommand = None
        self.message = SimpleNamespace(author=self.user, channel=self.channel)

    async def send(self, *args, **kwargs):
        normalized_args = args
        if not normalized_args and "embed" in kwargs:
            normalized_args = (kwargs["embed"],)
        elif not normalized_args and "content" in kwargs:
            normalized_args = (kwargs["content"],)

        payload = {"args": normalized_args, **kwargs}
        self.sent_messages.append(payload)
        return payload

    def typing(self):
        return self.channel.typing()



class FakeBot:
    def __init__(self) -> None:
        self.user = SimpleNamespace(
            id=999999,
            name="TestBot",
            avatar=SimpleNamespace(url="https://example.com/avatar.png"),
        )
        self.guilds = []
        self.application_info = lambda: None

    async def wait_until_ready(self) -> None:
        return None

    async def wait_for_message(self, *args, **kwargs):
        return None

    def get_channel(self, channel_id):
        return FakeChannel(channel_id=channel_id)

    def get_all_members(self):
        return []

    def get_user(self, user_id):
        return None

    def get_guild(self, guild_id):
        return None


async def invoke_command(command_obj: Any, cog: Any, interaction: FakeInteraction, **kwargs: Any) -> None:
    callback = getattr(command_obj, "callback", command_obj)
    if asyncio.iscoroutinefunction(callback):
        await callback(cog, interaction, **kwargs)
    else:
        callback(cog, interaction, **kwargs)


def get_application_command(cog: Any, name: str) -> Any:
    return next(command for command in cog.application_commands if command.name == name)


def build_cog(cog_cls: type, **kwargs: Any) -> Any:
    cog = object.__new__(cog_cls)

    if cog_cls is Utility:
        cog._Utility__bot = FakeBot()
        cog._Utility__admins = kwargs.get("admins", [])
    elif cog_cls is Games:
        cog._Games__bot = FakeBot()
        cog._Games__heroes = []
    elif cog_cls is Roles:
        cog._Roles__bot = FakeBot()
    else:
        raise TypeError(f"Unsupported cog {cog_cls}")

    if hasattr(cog, "_read_application_commands"):
        cog._read_application_commands()

    return cog


def ensure_test_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
