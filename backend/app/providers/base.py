"""Interfaces des fournisseurs IA. Le pipeline ne connaît que ces deux contrats."""
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    images: int = 0


@dataclass
class TextResult:
    data: dict
    usage: Usage = field(default_factory=Usage)


@dataclass
class ImageResult:
    image: bytes
    mime: str
    usage: Usage = field(default_factory=lambda: Usage(images=1))


class ContentBlocked(Exception):
    """Le filtre de sécurité du fournisseur a refusé la demande."""


class ProviderError(Exception):
    """Échec technique (réseau, quota, réponse illisible)."""


class TextProvider(Protocol):
    name: str

    async def json(
        self, *, model: str, system: str, user: str, schema: dict, schema_name: str,
        images: list[tuple[bytes, str]] | None = None, max_tokens: int = 16000,
    ) -> TextResult:
        """Un appel à sortie structurée : la réponse respecte `schema`.
        `images` : (octets, type MIME) pour les modèles vision."""
        ...


class ImageProvider(Protocol):
    name: str

    async def draw(
        self, *, model: str, prompt: str, references: list[tuple[bytes, str]], size: str = "1024x1536",
    ) -> ImageResult:
        """Dessine une image, guidée par des images de référence (fiches, photo)."""
        ...
