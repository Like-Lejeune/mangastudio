"""Point d'entrée de l'API : `uvicorn app.main:app --reload`."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app import checks
from app.config import get_settings
from app.db import init_db
from app.routers import (
    admin,
    admin_ops,
    auth,
    billing,
    episodes,
    series,
    sharing,
    testimonials,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()   # développement ; en production, migrations Alembic
    yield


settings = get_settings()
checks.run(settings)   # en production : refuse de démarrer avec une configuration dangereuse
prod = settings.is_production
# En production, la documentation interactive n'est pas publiée.
app = FastAPI(title="MangaStudio API", lifespan=lifespan,
              docs_url=None if prod else "/docs", redoc_url=None, openapi_url=None if prod else "/openapi.json")
app.add_middleware(
    CORSMiddleware,
    # En développement, un front lancé en local (n'importe quel port) peut appeler l'API.
    # En production, seules les adresses de FRONTEND_URL sont acceptées.
    allow_origin_regex=None if prod else r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_origins=[o.strip() for o in settings.frontend_url.split(",") if o.strip()],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"],
)

for module in (auth, series, episodes, billing, admin, admin_ops, testimonials, sharing):
    app.include_router(module.router)

# Images en local. En production : stockage S3/R2 et URL signées.
Path(settings.storage_dir).mkdir(parents=True, exist_ok=True)
app.mount("/files", StaticFiles(directory=settings.storage_dir), name="files")


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/", include_in_schema=False)
async def root():
    """L'API n'a pas de page d'accueil : documentation en développement, site en production."""
    return RedirectResponse(settings.frontend_url.split(",")[0].strip() if prod else "/docs")
