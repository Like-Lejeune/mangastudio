"""Plans d'abonnement : limites créatives et crédits. Prix = hypothèses à valider."""
from dataclasses import dataclass

MIN_PAGES = 4


@dataclass(frozen=True)
class Plan:
    id: str
    name: str
    credits: int            # par mois (plan gratuit : une seule fois, à l'inscription)
    max_characters: int     # par épisode
    max_pages: int          # par épisode
    color: bool
    redraw: bool
    price_usd_cents: int
    price_xaf: int


PLANS: dict[str, Plan] = {
    "free": Plan("free", "Découverte", 12, 3, 5, False, False, 0, 0),
    "creator": Plan("creator", "Créateur", 100, 6, 12, True, True, 999, 6000),
    "studio": Plan("studio", "Studio", 300, 10, 24, True, True, 2999, 18000),
}

# Pack de crédits à l'unité (n'expire pas).
PACK_CREDITS = 50
PACK_PRICE_USD_CENTS = 599
PACK_PRICE_XAF = 3500

PERIOD_DAYS = 30


def get_plan(plan_id: str | None) -> Plan:
    return PLANS.get(plan_id or "free", PLANS["free"])
