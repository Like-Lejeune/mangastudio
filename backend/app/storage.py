"""Stockage des images. Disque local ici ; remplacer par S3/R2 en production
en gardant les trois mêmes fonctions."""
import asyncio
import shutil
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


async def remove_folders(rels: list[str]) -> None:
    """Supprime les dossiers qui contiennent ces fichiers (anciennes versions comprises), sans erreur s'ils n'existent plus."""
    root = _root().resolve()
    for folder in {(root / rel).parent.resolve() for rel in rels}:
        if folder != root and root in folder.parents:      # jamais hors du stockage, jamais sa racine
            await asyncio.to_thread(shutil.rmtree, folder, True)


async def remove_prefix(key: str) -> None:
    """Supprime tout un dossier du stockage (ex. « series/<id> »), sans erreur s'il n'existe pas."""
    root = _root().resolve()
    folder = (root / key).resolve()
    if folder != root and root in folder.parents:
        await asyncio.to_thread(shutil.rmtree, folder, True)


def url(rel: str | None) -> str | None:
    return f"{get_settings().public_base_url}/files/{rel}" if rel else None
