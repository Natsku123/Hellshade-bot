from core.config import settings
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine


DATABASE_URL = f"postgresql+asyncpg://{settings.DATABASE_USER}:" \
               f"{settings.DATABASE_PASSWORD}@{settings.DATABASE_SERVER}/" \
               f"{settings.DATABASE_NAME}"

engine = create_async_engine(DATABASE_URL)

Base = declarative_base()
