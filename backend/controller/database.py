from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings


SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600)

Session = sessionmaker(
    autocommit=False,
    autoflush=True,
    bind=engine
)
Base = declarative_base()
