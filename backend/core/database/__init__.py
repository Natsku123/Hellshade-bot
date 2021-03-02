import asyncio

from config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine(settings.DATABASE_URL)

Session = scoped_session(sessionmaker(autoflush=False, bind=engine))

Base = declarative_base()
Base.query = Session.query_property()

session_lock = asyncio.Lock()
