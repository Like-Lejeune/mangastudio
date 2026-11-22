"""Corps des requêtes de l'API."""
from typing import Literal

from pydantic import BaseModel, Field


class Register(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=255)
    display_name: str = Field(min_length=1, max_length=60)
    password: str = Field(min_length=8, max_length=200)


class VerifyIn(BaseModel):
    code: str = Field(pattern=r"^\s*\d{6}\s*$")


class ForgotIn(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=255)


class ResetIn(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=255)
    code: str = Field(pattern=r"^\s*\d{6}\s*$")
    password: str = Field(min_length=8, max_length=200)


class Login(BaseModel):
    email: str
    password: str


class SeriesIn(BaseModel):
    premise: str = Field(min_length=8, max_length=1500)
    style: Literal["shonen", "shojo", "seinen", "kodomo", "afro"] = "shonen"
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
    product: Literal["creator", "studio", "pack", "don"]
    # Pour un don seulement : montant libre en FCFA.
    amount: int | None = Field(default=None, ge=500, le=1_000_000)
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


class AdminCreditsIn(BaseModel):
    amount: int = Field(ge=-100_000, le=100_000)   # négatif : retrait
    reason: str = Field(min_length=3, max_length=200)


class AdminPlanIn(BaseModel):
    plan: Literal["free", "creator", "studio"]
    days: int = Field(default=30, ge=1, le=366)
    grant_credits: bool = True
    reason: str = Field(min_length=3, max_length=200)


class AdminStatusIn(BaseModel):
    active: bool
    reason: str = Field(min_length=3, max_length=200)


class AdminRoleIn(BaseModel):
    is_admin: bool


class TestimonialIn(BaseModel):
    text: str = Field(min_length=10, max_length=280)
    rating: int = Field(ge=1, le=5)
    display_name: str = Field(min_length=2, max_length=60)
    role: str = Field(default="", max_length=80)
    consent: bool
    episode_id: str | None = None


class TestimonialStatusIn(BaseModel):
    status: Literal["approved", "rejected", "pending"]
