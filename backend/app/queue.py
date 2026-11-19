"""Lancement des tâches de fond.
Avec REDIS_URL : file ARQ (worker séparé, voir app/worker.py). Sans : tâche asyncio
dans le processus de l'API, suffisant en développement."""
import asyncio

from app.config import get_settings

_tasks: set[asyncio.Task] = set()   # garde une référence, sinon la tâche peut être ramassée


async def enqueue(job: str, *args) -> None:
    settings = get_settings()
    if settings.redis_url:
        from arq import create_pool
        from arq.connections import RedisSettings

        pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        await pool.enqueue_job(job, *args)
        await pool.aclose()
        return
    from app.pipeline import runner

    task = asyncio.create_task(getattr(runner, job)(*args))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
