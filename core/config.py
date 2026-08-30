import logging
import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_int_list(value: str | None) -> list[int]:
    if not value:
        return []

    normalized = value.strip()
    if normalized.startswith("[") and normalized.endswith("]"):
        normalized = normalized[1:-1].strip()

    if not normalized:
        return []

    return [int(item.strip()) for item in normalized.split(",") if item.strip()]


class Settings(BaseSettings):
    BOT_TOKEN: str = Field(default_factory=lambda: os.getenv("BOT_TOKEN") or os.getenv("TOKEN", ""))
    BOT_OWNER: int = int(os.getenv("OWNER", "0"))
    DATABASE_SERVER: str = os.environ.get("DB_HOST", "db")
    DATABASE_USER: str = os.getenv("DB_USER", "")
    DATABASE_PASSWORD: str = os.getenv("DB_PASS", "")
    DATABASE_NAME: str = os.getenv("DB_NAME", "")
    ADMINS: list[int] = _parse_int_list(os.getenv("ADMINS", ""))
    URL: str = os.getenv("SITE_URL", "https://bot.hellshade.fi")
    STEAM_API_KEY: str = os.getenv("STEAM_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    model_config = SettingsConfigDict(case_sensitive=True)


settings = Settings()


logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
)
logger.addHandler(handler)
