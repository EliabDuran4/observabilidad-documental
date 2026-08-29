from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

Base = declarative_base()

engine_shard1 = create_engine(settings.database_url_shard1)
engine_shard2 = create_engine(settings.database_url_shard2)

engine_shard1_replica = create_engine(settings.database_url_shard1_replica)
engine_shard2_replica = create_engine(settings.database_url_shard2_replica)

SessionShard1Replica = sessionmaker(autocommit=False, autoflush=False, bind=engine_shard1_replica)
SessionShard2Replica = sessionmaker(autocommit=False, autoflush=False, bind=engine_shard2_replica)


def get_replica_session_for_year(year: int):
    return SessionShard2Replica() if year >= settings.shard_year_threshold else SessionShard1Replica()

SessionShard1 = sessionmaker(autocommit=False, autoflush=False, bind=engine_shard1)
SessionShard2 = sessionmaker(autocommit=False, autoflush=False, bind=engine_shard2)


def get_engine_for_year(year: int):
    return engine_shard2 if year >= settings.shard_year_threshold else engine_shard1


def get_session_for_year(year: int):
    return SessionShard2() if year >= settings.shard_year_threshold else SessionShard1()


def get_db():
    """Sesión por defecto (shard1) para dependencias que no requieren year explícito, ej. crear tablas."""
    db = SessionShard1()
    try:
        yield db
    finally:
        db.close()