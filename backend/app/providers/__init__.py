"""Registre : quel fournisseur et quel modèle pour chaque rôle, d'après la configuration.
Ajouter un fournisseur = une classe + une ligne dans _text() / _image()."""
from dataclasses import dataclass

from app.config import get_settings
from app.providers.base import ImageProvider, TextProvider
from app.providers.fake import FakeImage, FakeText
from app.providers.meta_muse import MuseImage, MuseText
from app.providers.openai_compat import OpenAICompatImage, OpenAICompatText


def _text(name: str) -> TextProvider:
    s = get_settings()
    if name == "fake":
        return FakeText()
    if name == "openai_compat":
        return OpenAICompatText(s.openai_compat_base_url, s.openai_compat_api_key)
    if name == "meta_muse":
        return MuseText(s.meta_api_base, s.meta_api_key)
    raise ValueError(f"Fournisseur de texte inconnu : {name}")


def _image(name: str) -> ImageProvider:
    s = get_settings()
    if name == "fake":
        return FakeImage()
    if name == "openai_compat":
        return OpenAICompatImage(s.openai_compat_base_url, s.openai_compat_api_key)
    if name == "meta_muse":
        return MuseImage(s.meta_api_base, s.meta_api_key)
    raise ValueError(f"Fournisseur d'image inconnu : {name}")


@dataclass
class Studio:
    """Les trois rôles du pipeline. Les tests en construisent un avec leurs propres doublures."""
    writer: TextProvider
    writer_model: str
    checker: TextProvider
    checker_model: str
    artist: ImageProvider
    artist_model: str
    max_refs: int


def get_studio() -> Studio:
    s = get_settings()
    return Studio(
        writer=_text(s.writer_provider), writer_model=s.writer_model,
        checker=_text(s.checker_provider), checker_model=s.checker_model,
        artist=_image(s.image_provider), artist_model=s.image_model,
        max_refs=s.image_max_refs,
    )
