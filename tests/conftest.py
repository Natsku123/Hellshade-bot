import os
import sys
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_test_env() -> None:
    env_path = ROOT / ".env.test"
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_test_env()

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_USER"] = "test"
os.environ["DB_PASS"] = "test"
os.environ["DB_NAME"] = "test"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


Games: Any
Roles: Any
Utility: Any
FakeInteraction: Any
FakeUser: Any
build_cog: Any
ensure_test_database: Any


def _import_test_dependencies() -> None:
    global Games, Roles, Utility, FakeInteraction, FakeUser, build_cog, ensure_test_database

    Games = import_module("core.cogs.games").Games
    Roles = import_module("core.cogs.roles").Roles
    Utility = import_module("core.cogs.utility").Utility

    discord_harness = import_module("tests.support.discord_harness")
    FakeInteraction = discord_harness.FakeInteraction
    FakeUser = discord_harness.FakeUser
    build_cog = discord_harness.build_cog
    ensure_test_database = discord_harness.ensure_test_database


_import_test_dependencies()


def pytest_addoption(parser):
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="Run tests marked as live (requires real Discord integration setup).",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-live"):
        return

    skip_live = pytest.mark.skip(reason="need --run-live option to run live Discord tests")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture(autouse=True)
def _reset_database():
    ensure_test_database()
    yield
    ensure_test_database()


@pytest.fixture
def utility_cog():
    return build_cog(Utility, admins=[123456])


@pytest.fixture
def games_cog():
    return build_cog(Games)


@pytest.fixture
def roles_cog():
    return build_cog(Roles)


@pytest.fixture
def interaction_factory():
    def _build(user_id: int = 1, name: str = "tester") -> FakeInteraction:
        return FakeInteraction(user=FakeUser(id=user_id, name=name))

    return _build
