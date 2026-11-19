"""Point d'entrée de l'API : `uvicorn app.main:app --reload`."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db import init_db
from app.routers import admin, auth, billing, episodes, series


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()   # développement ; en production, migrations Alembic
    yield


settings = get_settings()
app = FastAPI(title="MangaStudio API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    # Un front lancé en local (n'importe quel port) peut toujours appeler l'API : l'accès repose sur le jeton, pas sur des cookies.
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_origins=[o.strip() for o in settings.frontend_url.split(",") if o.strip()], allow_methods=["*"], allow_headers=["*"],
)

for module in (auth, series, episodes, billing, admin):
    app.include_router(module.router)

# Images en local. En production : stockage S3/R2 et URL signées.
Path(settings.storage_dir).mkdir(parents=True, exist_ok=True)
app.mount("/files", StaticFiles(directory=settings.storage_dir), name="files")


@app.get("/health")
async def health():
    return {"ok": True}
