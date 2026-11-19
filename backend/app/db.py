"""Moteur SQLAlchemy asynchrone et session par requête."""
import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(get_settings().database_url)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Révision qui décrit le schéma tel qu'il était avant l'arrivée des migrations.
FIRST_REVISION = "0001"


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


def _alembic_config():
    from alembic.config import Config

    backend = Path(__file__).resolve().parent.parent
    config = Config(str(backend / "alembic.ini"))
    config.set_main_option("script_location", str(backend / "migrations"))
    return config


async def init_db() -> None:
    """Met la base au niveau du code en appliquant les migrations en attente.

    Appelé au démarrage de l'API. Une base créée avant l'arrivée des migrations
    (tables présentes, pas de table alembic_version) est complétée puis marquée
    comme étant à la première révision, puis mise à niveau comme les autres."""
    from alembic import command

    from app import models  # noqa: F401  (enregistre les tables)

    async with engine.begin() as conn:
        tables = await conn.run_sync(lambda c: set(inspect(c).get_table_names()))
        if "users" in tables and "alembic_version" not in tables:
            await conn.run_sync(Base.metadata.create_all)
            legacy = True
        else:
            legacy = False
    config = _alembic_config()
    # Alembic ouvre sa propre boucle asyncio : on l'exécute dans un fil séparé.
    if legacy:
        await asyncio.to_thread(command.stamp, config, FIRST_REVISION)
    await asyncio.to_thread(command.upgrade, config, "head")
