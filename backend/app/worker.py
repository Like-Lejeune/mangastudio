"""Worker ARQ : `arq app.worker.WorkerSettings` (nécessite REDIS_URL)."""
from arq.connections import RedisSettings

from app.config import get_settings
from app.pipeline import runner


async def run_episode(ctx, episode_id: str) -> None:
    await runner.run_episode(episode_id)


async def redraw_page(ctx, page_id: str, note: str) -> None:
    await runner.redraw_page(page_id, note)


class WorkerSettings:
    functions = [run_episode, redraw_page]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url or "redis://localhost:6379")
    job_timeout = 1800      # un épisode de 24 pages peut prendre plusieurs minutes
    max_jobs = 4
