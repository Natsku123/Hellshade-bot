import asyncio

from core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = f"postgresql://{settings.DATABASE_USER}:" \
               f"{settings.DATABASE_PASSWORD}@{settings.DATABASE_SERVER}/" \
               f"{settings.DATABASE_NAME}"

engine = create_engine(DATABASE_URL)

Session = sessionmaker(autoflush=False, bind=engine)

Base = declarative_base()

session_lock = asyncio.Lock()
