# Test suite

This directory contains the regression and integration tests for the bot command surface.

## Structure

- [test_command_dispatch.py](test_command_dispatch.py) - Fast, deterministic tests for command dispatch and handler behavior using the fake Discord harness.
- [test_regression.py](test_regression.py) - Regression tests for role-related flows and other higher-level behavior.
- [test_discord_live.py](test_discord_live.py) - Optional live Discord integration tests that exercise real Discord API behavior.
- [support/discord_harness.py](support/discord_harness.py) - Shared test doubles for users, interactions, channels, and guild state.
- [conftest.py](conftest.py) - Pytest fixtures, database reset helpers, and environment bootstrap.

## Running the tests

Run the full suite from the repository root:

```bash
uv run pytest
# or
make test
```

Run the fast command-dispatch coverage suite:

```bash
uv run pytest tests/test_command_dispatch.py
# or
make test-dispatch
```

Run the regression suite:

```bash
uv run pytest tests/test_regression.py
# or
make test-regression
```

Run only tests marked as live (still skipped by default unless enabled):

```bash
uv run pytest -m live
# or
make test-live
```

Run the live Discord integration suite explicitly:

```bash
uv run pytest --run-live tests/test_discord_live.py
# or
make test-live-enabled
```

Run all tests with coverage:

```bash
make test-cov
```

## Notes

- The fast tests use the in-memory SQLite test database and fake Discord objects, so they are suitable for local regression checks.
- The live Discord tests require a real bot token and access to a guild where the bot can manage roles.
- Required env for live tests: `TOKEN` (or `BOT_TOKEN`) and `TEST_GUILD_ID`.
- Live tests are gated behind `--run-live` and `@pytest.mark.live`.
- Tests that change Discord state should be kept in the live suite or explicitly marked as integration tests.
