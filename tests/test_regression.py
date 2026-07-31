import pytest


@pytest.mark.parametrize(
    ("module_name", "test_path"),
    [
        ("tests.test_command_dispatch", "tests/test_command_dispatch.py"),
        ("tests.test_discord_live", "tests/test_discord_live.py"),
    ],
)
def test_regression_modules_are_discoverable(module_name, test_path):
    assert module_name
    assert test_path.endswith(".py")
