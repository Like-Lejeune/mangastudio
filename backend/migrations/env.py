"""Environnement Alembic : lit DATABASE_URL dans la configuration de l'application
et compare la base aux modèles de app/models.py."""
import asyncio

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app import models  # noqa: F401  (enregistre les tables)
from app.config import get_settings
from app.db import Base

# Pas de logging.config.fileConfig ici : il couperait les journaux de l'API quand les migrations tournent au démarrage.


def run(connection) -> None:
    context.configure(
        connection=connection, target_metadata=Base.metadata, compare_type=True,
        render_as_batch=True,   # SQLite ne sait pas modifier une colonne : Alembic recrée la table
    )
    with context.begin_transaction():
        context.run_migrations()


async def main() -> None:
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(run)
    await engine.dispose()


asyncio.run(main())
