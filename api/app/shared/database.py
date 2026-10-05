import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://marketplace:marketplace@127.0.0.1:5432/marketplace")
# Vercel/Neon inject plain postgresql:// (or postgres://); force the psycopg3 driver.
DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1).replace("postgresql://", "postgresql+psycopg://", 1)


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", "2")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "1")),
    pool_recycle=300,
    pool_use_lifo=True,
)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as db:
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
