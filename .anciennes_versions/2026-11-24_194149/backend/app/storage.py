"""Stockage des images. Disque local ici ; remplacer par S3/R2 en production
en gardant les trois mêmes fonctions."""
import asyncio
from pathlib import Path

from app.config import get_settings

EXT = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/svg+xml": "svg"}


def _root() -> Path:
    root = Path(get_settings().storage_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


async def save(key: str, data: bytes, mime: str) -> str:
    """Enregistre `data` sous `key` (sans extension) et renvoie le chemin relatif."""
    rel = f"{key}.{EXT.get(mime, 'bin')}"
    path = _root() / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(path.write_bytes, data)
    return rel


async def load(rel: str) -> bytes:
    return await asyncio.to_thread((_root() / rel).read_bytes)


def url(rel: str | None) -> str | None:
    return f"{get_settings().public_base_url}/files/{rel}" if rel else None
