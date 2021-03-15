import logging
import os
from typing import List

from pydantic import BaseSettings, AnyHttpUrl


class Settings(BaseSettings):
    BOT_TOKEN: str = os.environ.get("TOKEN")
    BOT_OWNER: int = os.environ.get("OWNER")
    DATABASE_SERVER: str = os.environ.get("DB_HOST", "db")
    DATABASE_USER: str = os.environ.get("DB_USER")
    DATABASE_PASSWORD: str = os.environ.get("DB_PASS")
    DATABASE_NAME: str = os.environ.get("DB_NAME")
    ADMINS: List[int] = os.environ.get('ADMINS').split(",")
    URL: AnyHttpUrl = os.environ.get('SITE_URL', 'https://bot.hellshade.fi')

    class Config:
        case_sensitive = True


settings = Settings()


logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
)
logger.addHandler(handler)
