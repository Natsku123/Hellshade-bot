from core.config import Settings


def test_settings_reads_bot_token_from_bot_token_env(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "from-bot-token")
    monkeypatch.delenv("TOKEN", raising=False)

    settings = Settings()

    assert settings.BOT_TOKEN == "from-bot-token"


def test_settings_falls_back_to_legacy_token_env(monkeypatch) -> None:
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    monkeypatch.setenv("TOKEN", "from-token")

    settings = Settings()

    assert settings.BOT_TOKEN == "from-token"
