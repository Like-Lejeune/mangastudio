"""Tableau de bord d'administration : accès, chiffres, gestion des comptes, journal."""
import asyncio

import pytest
from sqlalchemy import update

from app.db import SessionLocal
from app.models import User


async def account(client, email, password="motdepasse"):
    r = await client.post("/auth/register", json={"email": email, "display_name": email.split("@")[0], "password": password})
    if r.status_code == 409:
        r = await client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture
async def admin(client):
    """Un compte administrateur, quel que soit l'ordre des tests (le premier compte créé n'est pas forcément celui-ci)."""
    h = await account(client, "admin@test.cm")
    async with SessionLocal() as session:
        await session.execute(update(User).where(User.email == "admin@test.cm").values(is_admin=True))
        await session.commit()
    assert (await client.get("/me", headers=h)).json()["is_admin"]
    return h


async def test_admin_only(client, admin):
    user = await account(client, "simple@test.cm")
    for path in ("/admin/overview", "/admin/users", "/admin/episodes", "/admin/payments", "/admin/payment-intents", "/admin/actions"):
        assert (await client.get(path, headers=user)).status_code == 403, path
        assert (await client.get(path, headers=admin)).status_code == 200, path


async def test_overview_shape(client, admin):
    o = (await client.get("/admin/overview", headers=admin)).json()
    assert o["users"]["total"] >= 1 and len(o["daily"]) == 30
    assert {"signups", "episodes", "revenue_xaf", "cost_usd"} <= set(o["daily"][0])
    assert o["daily"][-1]["signups"] >= 1          # au moins un compte créé aujourd'hui


async def test_manage_user(client, admin):
    target = await account(client, "client@test.cm")
    me = (await client.get("/me", headers=target)).json()
    uid = me["id"]

    found = (await client.get("/admin/users", params={"q": "client@"}, headers=admin)).json()
    assert found["total"] == 1 and found["items"][0]["id"] == uid

    # Crédits : ajout puis retrait, jamais sous zéro
    r = await client.post(f"/admin/users/{uid}/credits", json={"amount": 30, "reason": "geste commercial"}, headers=admin)
    assert r.json()["credits"] == me["credits"] + 30
    r = await client.post(f"/admin/users/{uid}/credits", json={"amount": -10, "reason": "correction"}, headers=admin)
    assert r.json()["credits"] == me["credits"] + 20
    r = await client.post(f"/admin/users/{uid}/credits", json={"amount": -10_000, "reason": "trop"}, headers=admin)
    assert r.status_code == 422

    # Plan offert, puis retour au gratuit
    await client.post(f"/admin/users/{uid}/plan", json={"plan": "studio", "days": 7, "grant_credits": True, "reason": "partenaire"}, headers=admin)
    assert (await client.get("/me", headers=target)).json()["plan"]["id"] == "studio"
    await client.post(f"/admin/users/{uid}/plan", json={"plan": "free", "reason": "fin du partenariat"}, headers=admin)
    assert (await client.get("/me", headers=target)).json()["plan"]["id"] == "free"

    # Suspension : plus d'accès ni de connexion ; réactivation
    await client.post(f"/admin/users/{uid}/status", json={"active": False, "reason": "fraude au paiement"}, headers=admin)
    r = await client.get("/me", headers=target)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "account_suspended"
    assert (await client.post("/auth/login", json={"email": "client@test.cm", "password": "motdepasse"})).status_code == 403
    await client.post(f"/admin/users/{uid}/status", json={"active": True, "reason": "vérifié"}, headers=admin)
    assert (await client.get("/me", headers=target)).status_code == 200

    # Rôle
    await client.post(f"/admin/users/{uid}/role", json={"is_admin": True}, headers=admin)
    assert (await client.get("/admin/overview", headers=target)).status_code == 200
    await client.post(f"/admin/users/{uid}/role", json={"is_admin": False}, headers=admin)
    assert (await client.get("/admin/overview", headers=target)).status_code == 403

    # Tout est au journal, et sur la fiche
    detail = (await client.get(f"/admin/users/{uid}", headers=admin)).json()
    kinds = [a["action"] for a in detail["admin_actions"]]
    assert kinds.count("credits") == 2 and kinds.count("plan") == 2 and "suspend" in kinds and "reactivate" in kinds
    assert any(c["note"] == "admin : geste commercial" for c in detail["ledger"])
    journal = (await client.get("/admin/actions", headers=admin)).json()
    assert journal["total"] >= 8


async def test_admin_cannot_lock_himself_out(client, admin):
    me = (await client.get("/me", headers=admin)).json()
    assert (await client.post(f"/admin/users/{me['id']}/status", json={"active": False, "reason": "test"}, headers=admin)).status_code == 422
    assert (await client.post(f"/admin/users/{me['id']}/role", json={"is_admin": False}, headers=admin)).status_code == 422


async def test_episode_visible_to_admin(client, admin):
    owner = await account(client, "auteur@test.cm")
    sid = (await client.post("/series", headers=owner, json={"premise": "Une histoire de marché à Mokolo."})).json()["id"]
    cid = (await client.post(f"/series/{sid}/characters", headers=owner, json={"name": "Awa"})).json()["id"]
    eid = (await client.post(f"/series/{sid}/episodes", headers=owner, json={"page_count": 4, "character_ids": [cid]})).json()["id"]
    for _ in range(200):
        if (await client.get(f"/episodes/{eid}", headers=owner)).json()["status"] == "done":
            break
        await asyncio.sleep(0.05)
    listed = (await client.get("/admin/episodes", params={"q": "auteur@"}, headers=admin)).json()
    assert listed["items"][0]["id"] == eid and listed["items"][0]["credits"] > 0
    detail = (await client.get(f"/admin/episodes/{eid}", headers=admin)).json()
    assert detail["owner"]["email"] == "auteur@test.cm" and len(detail["pages"]) == 4 and detail["cost"]
    # L'épisode reste invisible pour un autre utilisateur
    other = await account(client, "curieux@test.cm")
    assert (await client.get(f"/episodes/{eid}", headers=other)).status_code == 404


async def test_moderation_changes_are_logged(client, admin):
    await client.post("/admin/terms", json={"term": "Arnaque", "action": "flag"}, headers=admin)
    journal = (await client.get("/admin/actions", headers=admin)).json()["items"]
    assert any(a["action"] == "term" and "arnaque" in a["detail"] for a in journal)
