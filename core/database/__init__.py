import asyncio

from core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool


DATABASE_URL = settings.DATABASE_URL or (
    f"postgresql://{settings.DATABASE_USER}:"
    f"{settings.DATABASE_PASSWORD}@{settings.DATABASE_SERVER}/"
    f"{settings.DATABASE_NAME}"
)

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update(
        {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }
    )

engine = create_engine(DATABASE_URL, **engine_kwargs)

Session = sessionmaker(autoflush=False, bind=engine)

Base = declarative_base()

session_lock = asyncio.Lock()
