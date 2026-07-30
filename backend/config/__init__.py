import os
from pydantic_settings import BaseSettings


def _get_origins() -> list[str]:
    raw_origins = os.environ.get("ORIGINS")
    if raw_origins:
        return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

    origins = ["http://localhost:3080", "http://localhost:8080"]
    site_url = os.environ.get("SITE_URL")
    if site_url:
        origins.append(site_url)
    return origins


class Settings(BaseSettings):
    SERVER_NAME: str = os.environ.get("SERVER_NAME", "Hellshade-bot")
    DATABASE_URL: str = os.environ.get(
        "DB_URL",
        f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASS')}@db/{os.environ.get('DB_NAME')}",
    )
    ORIGINS: list[str] = _get_origins()

    class Config:
        case_sensitive = True


settings = Settings()
