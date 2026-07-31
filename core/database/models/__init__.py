from importlib import import_module

from core.database import Base as Base


_MODEL_EXPORTS = {
    "Member": "core.database.models.members",
    "Level": "core.database.models.levels",
    "Player": "core.database.models.players",
    "Server": "core.database.models.servers",
    "User": "core.database.models.users",
    "Role": "core.database.models.roles",
    "RoleEmoji": "core.database.models.roles",
    "Subscription": "core.database.models.steamnews",
    "Post": "core.database.models.steamnews",
    "Command": "core.database.models.commands",
    "DotaGuild": "core.database.models.dota_guild",
}

__all__ = [
    "Base",
    "Member",
    "Level",
    "Player",
    "Server",
    "User",
    "Role",
    "RoleEmoji",
    "Subscription",
    "Post",
    "Command",
    "DotaGuild",
]


def __getattr__(name: str):
    if name in _MODEL_EXPORTS:
        module = import_module(_MODEL_EXPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

