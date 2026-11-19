"""Corps des requêtes de l'API."""
from typing import Literal

from pydantic import BaseModel, Field


class Register(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=255)
    display_name: str = Field(min_length=1, max_length=60)
    password: str = Field(min_length=8, max_length=200)


class Login(BaseModel):
    email: str
    password: str


class SeriesIn(BaseModel):
    premise: str = Field(min_length=8, max_length=1500)
    style: Literal["shonen", "shojo", "seinen", "kodomo"] = "shonen"
    palette: Literal["bw", "color"] = "bw"
    language: Literal["fr", "en"] = "fr"


class CharacterIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    role: str = Field(default="", max_length=120)
    description: str = Field(default="", max_length=600)
    # Photo en data URL (JPEG, PNG ou WebP), facultative.
    photo: str | None = Field(default=None, max_length=4_000_000)
    # Obligatoire avec une photo : l'utilisateur déclare avoir l'accord de la personne.
    consent: bool = False


class EpisodeIn(BaseModel):
    direction: str = Field(default="", max_length=800)
    page_count: int
    character_ids: list[str] = Field(min_length=1)


class RedrawIn(BaseModel):
    note: str = Field(min_length=3, max_length=300)


class CheckoutIn(BaseModel):
    product: Literal["creator", "studio", "pack"]
    provider: Literal["trust", "stripe"] = "trust"
    # Mobile money (trust) : numéro du payeur et code de l'opérateur, pris dans GET /billing/operators.
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9 ]{8,18}$")
    operator: str | None = Field(default=None, max_length=40)


class TermIn(BaseModel):
    term: str = Field(min_length=2, max_length=120)
    action: Literal["block", "flag"] = "block"


class SceneRuleIn(BaseModel):
    label: str = Field(min_length=2, max_length=60)
    description: str = Field(min_length=5, max_length=500)
    active: bool = True
