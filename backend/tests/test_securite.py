"""Sécurité : tentatives de connexion, administrateurs par adresse, photos, contrôles de production, plafond IA."""
import base64

from sqlalchemy import delete

from app import checks
from app.config import Settings, get_settings
from app.db import SessionLocal
from app.models import AdminAction, UsageEvent

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


async def compte(client, email, password="motdepasse"):
    r = await client.post("/auth/register", json={"email": email, "display_name": "x", "password": password})
    if r.status_code == 409:
        r = await client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['token']}"}


async def test_connexion_bloquee_apres_5_echecs(client):
    await compte(client, "cible@test.cm")
    for _ in range(5):
        assert (await client.post("/auth/login", json={"email": "cible@test.cm", "password": "mauvais"})).status_code == 401
    r = await client.post("/auth/login", json={"email": "cible@test.cm", "password": "motdepasse"})
    assert r.status_code == 429 and r.json()["detail"]["code"] == "too_many_attempts" and int(r.headers["Retry-After"]) > 0
    # Un autre compte depuis la même adresse reste accessible.
    assert (await client.post("/auth/login", json={"email": "autre@test.cm", "password": "x"})).status_code == 401


async def test_reussite_remet_le_compteur_a_zero(client):
    await compte(client, "distrait@test.cm")
    for _ in range(4):
        await client.post("/auth/login", json={"email": "distrait@test.cm", "password": "mauvais"})
    assert (await client.post("/auth/login", json={"email": "distrait@test.cm", "password": "motdepasse"})).status_code == 200
    for _ in range(4):
        assert (await client.post("/auth/login", json={"email": "distrait@test.cm", "password": "mauvais"})).status_code == 401


async def test_inscriptions_limitees_par_heure(client):
    limite = get_settings().register_max_per_hour
    codes = [(await client.post("/auth/register", json={"email": f"robot{i}@test.cm", "display_name": "r", "password": "motdepasse"})).status_code
             for i in range(limite + 1)]
    assert codes[:limite] == [201] * limite and codes[-1] == 429


async def test_premier_inscrit_pas_admin_mais_admin_emails_oui(client, monkeypatch):
    h = await compte(client, "quelconque@test.cm")
    assert not (await client.get("/me", headers=h)).json()["is_admin"]
    monkeypatch.setattr(get_settings(), "admin_emails", "patron@test.cm, quelconque@test.cm")
    assert (await client.get("/me", headers=await compte(client, "patron@test.cm"))).json()["is_admin"]
    # Compte existant : promu à la connexion suivante.
    assert (await client.get("/me", headers=await compte(client, "quelconque@test.cm"))).json()["is_admin"]


async def _serie(client, h):
    return (await client.post("/series", json={"premise": "Une coursière de Yaoundé arrête le temps."}, headers=h)).json()["id"]


async def test_photo_controlee(client, monkeypatch):
    h = await compte(client, "photo@test.cm")
    sid = await _serie(client, h)
    perso = {"name": "Nadia", "consent": True}
    ok = await client.post(f"/series/{sid}/characters", json={**perso, "photo": "data:image/png;base64," + base64.b64encode(PNG).decode()}, headers=h)
    assert ok.status_code == 201
    faux = base64.b64encode(b"<?php system($_GET['c']); ?>").decode()
    assert (await client.post(f"/series/{sid}/characters", json={**perso, "name": "B", "photo": "data:image/png;base64," + faux}, headers=h)).status_code == 422
    assert (await client.post(f"/series/{sid}/characters", json={**perso, "name": "C", "photo": "data:image/png;base64,%%%"}, headers=h)).status_code == 422
    monkeypatch.setattr(get_settings(), "max_photo_bytes", 32)
    r = await client.post(f"/series/{sid}/characters", json={**perso, "name": "D", "photo": "data:image/png;base64," + base64.b64encode(PNG).decode()}, headers=h)
    assert r.status_code == 413


def test_controles_de_production():
    mauvais = Settings(environment="production", secret_key="court", frontend_url="http://localhost:5173",
                       database_url="sqlite+aiosqlite:///x.db", writer_provider="fake", _env_file=None)
    erreurs, _ = checks.problems(mauvais)
    assert len(erreurs) >= 4
    try:
        checks.run(mauvais)
        raise AssertionError("aurait dû refuser")
    except RuntimeError as e:
        assert "SECRET_KEY" in str(e)
    bon = Settings(environment="production", secret_key="a" * 64, frontend_url="https://app.exemple.cm",
                   public_base_url="https://api.exemple.cm", database_url="postgresql+asyncpg://u:p@db/m",
                   writer_provider="meta_muse", checker_provider="meta_muse", image_provider="meta_muse", meta_api_key="k",
                   admin_emails="moi@exemple.cm", ai_daily_budget_usd=20, prices={"m": {"in": 1}}, _env_file=None)
    assert checks.problems(bon)[0] == []
    checks.run(bon)


async def test_plafond_ia_refuse_et_alerte(client, monkeypatch):
    h = await compte(client, "budget@test.cm")
    sid = await _serie(client, h)
    perso = (await client.post(f"/series/{sid}/characters", json={"name": "Awa"}, headers=h)).json()["id"]
    from app import budget
    async with SessionLocal() as s:
        deja = await budget.spent_today(s)          # ce que les autres tests ont déjà « dépensé » aujourd'hui
    monkeypatch.setattr(get_settings(), "ai_daily_budget_usd", deja + 5.0)
    async with SessionLocal() as s:
        await s.execute(delete(AdminAction).where(AdminAction.action == "budget_alert"))
        s.add(UsageEvent(user_id="x", episode_id=None, stage="page", provider="p", model="m", cost_micro_usd=4_200_000))
        await s.commit()
    # 84 % : alerte, mais l'épisode passe encore.
    ok = await client.post(f"/series/{sid}/episodes", json={"page_count": 4, "character_ids": [perso]}, headers=h)
    assert ok.status_code == 202
    async with SessionLocal() as s:
        s.add(UsageEvent(user_id="x", episode_id=None, stage="page", provider="p", model="m", cost_micro_usd=1_000_000))
        await s.commit()
    import asyncio
    for _ in range(50):   # attendre la fin de l'épisode lancé
        if (await client.get(f"/episodes/{ok.json()['id']}", headers=h)).json()["status"] in ("done", "failed", "blocked"):
            break
        await asyncio.sleep(0.1)
    r = await client.post(f"/series/{sid}/episodes", json={"page_count": 4, "character_ids": [perso]}, headers=h)
    assert r.status_code == 503 and r.json()["detail"]["code"] == "daily_budget_reached"
    async with SessionLocal() as s:
        from sqlalchemy import select
        alertes = (await s.execute(select(AdminAction.target_id).where(AdminAction.action == "budget_alert"))).scalars().all()
        await s.execute(delete(UsageEvent).where(UsageEvent.user_id == "x"))
        await s.commit()
    assert any(a.endswith(":80") for a in alertes) and any(a.endswith(":100") for a in alertes)
    assert len(alertes) == 2   # une seule fois par niveau
