import os
from typing import List
from pydantic import BaseSettings, AnyHttpUrl


class Settings(BaseSettings):
    SERVER_NAME: str = os.environ.get("SERVER_NAME", "Hellshade-bot")
    DATABASE_URL: str = os.environ.get("DB_URL", f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASS')}@db/{os.environ.get('DB_NAME')}")
    ORIGINS: List[AnyHttpUrl] = os.environ.get("ORIGINS", ["http://localhost:3080", "http://localhost:8080", os.environ.get('SITE_URL')])

    class Config:
        case_sensitive = True


settings = Settings()
