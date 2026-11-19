"""Limite de tentatives en mémoire : fenêtre glissante par clé (IP, IP + compte…).

L'API tourne dans un seul processus (uvicorn sans --workers) : la mémoire suffit. Un redémarrage
remet les compteurs à zéro, ce qui est sans gravité pour cet usage."""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

_hits: dict[str, deque[float]] = defaultdict(deque)


def client_ip(request: Request) -> str:
    # Derrière Caddy, uvicorn --proxy-headers place déjà la vraie adresse du visiteur dans request.client.
    return request.client.host if request.client else "inconnue"


def _window(key: str, seconds: float) -> deque[float]:
    q = _hits[key]
    limit = time.monotonic() - seconds
    while q and q[0] <= limit:
        q.popleft()
    return q


def check(key: str, limit: int, seconds: float) -> None:
    """Refuse (429) si `key` a déjà atteint `limit` occurrences dans la fenêtre."""
    q = _window(key, seconds)
    if len(q) >= limit:
        wait = int(q[0] + seconds - time.monotonic()) + 1
        minutes = max(1, round(wait / 60))
        raise HTTPException(
            429,
            {"code": "too_many_attempts", "message": f"Trop de tentatives. Réessayez dans {minutes} minute{'s' if minutes > 1 else ''}.", "retry_after": wait},
            headers={"Retry-After": str(wait)},
        )


def add(key: str) -> None:
    _hits[key].append(time.monotonic())


def reset(key: str) -> None:
    _hits.pop(key, None)


def clear_all() -> None:
    """Pour les tests."""
    _hits.clear()
