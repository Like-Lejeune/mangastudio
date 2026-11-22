"""Parcours complet : limites du plan, génération, compteur, crédits, paiement, modération."""
import asyncio

from sqlalchemy import update

from app.db import SessionLocal
from app.models import Episode, User
from app.pipeline import runner
from app.providers import get_studio
from app.providers.base import TextResult, Usage
from app.providers.fake import FakeText
from tests.trust_fake import FakeTrust


async def wait_done(client, headers, episode_id):
    for _ in range(200):
        ep = (await client.get(f"/episodes/{episode_id}", headers=headers)).json()
        if ep["status"] in ("done", "failed", "blocked"):
            return ep
        await asyncio.sleep(0.05)
    raise AssertionError("épisode jamais terminé")


async def test_full_flow(client, monkeypatch):
    r = await client.post("/auth/register", json={"email": "a@b.cm", "display_name": "Yves", "password": "motdepasse"})
    h = {"Authorization": f"Bearer {r.json()['token']}"}
    me = (await client.get("/me", headers=h)).json()
    assert me["credits"] == 12 and me["plan"]["id"] == "free"
    # Administrateur pour la partie modération (le premier compte de la base l'est, mais l'ordre des tests varie).
    async with SessionLocal() as session:
        await session.execute(update(User).where(User.id == me["id"]).values(is_admin=True))
        await session.commit()

    # Plan gratuit : pas de couleur.
    r = await client.post("/series", headers=h, json={"premise": "Quatre amis ratent le dernier bus.", "palette": "color"})
    assert r.status_code == 403
    sid = (await client.post("/series", headers=h, json={"premise": "Quatre amis ratent le dernier bus à Yaoundé."})).json()["id"]
    chars = []
    for name in ["Awa", "Brice", "Chantal", "Didier", "Estelle", "Francis"]:
        r = await client.post(f"/series/{sid}/characters", headers=h, json={"name": name, "description": f"{name}, toujours en retard"})
        assert r.status_code == 201
        chars.append(r.json()["id"])

    # Limites du plan gratuit : 3 personnages, 5 pages.
    r = await client.post(f"/series/{sid}/episodes", headers=h, json={"page_count": 5, "character_ids": chars[:4]})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "plan_limit"
    r = await client.post(f"/series/{sid}/episodes", headers=h, json={"page_count": 6, "character_ids": chars[:3]})
    assert r.status_code == 403

    r = await client.post(f"/series/{sid}/episodes", headers=h, json={"page_count": 5, "character_ids": chars[:3]})
    assert r.status_code == 202
    ep = await wait_done(client, h, r.json()["id"])
    assert ep["status"] == "done", ep["error"]
    assert len(ep["pages"]) == 5 and all(p["url"] for p in ep["pages"])
    # Compteur : 3 fiches + 5 pages + 1 couverture = 9 images = 9 crédits ; des tokens par étape.
    u = ep["usage"]
    assert u["images"] == 9 and u["credits"] == 9 and u["input_tokens"] > 0 and u["output_tokens"] > 0
    assert {s["stage"] for s in u["stages"]} == {"script", "moderation", "sheet", "page", "check", "cover"}
    assert (await client.get("/me", headers=h)).json()["credits"] == 3

    # Plus assez de crédits pour un deuxième épisode.
    r = await client.post(f"/series/{sid}/episodes", headers=h, json={"page_count": 5, "character_ids": chars[:3]})
    assert r.status_code == 402 and r.json()["detail"]["needed"] == 5

    # Paiement mobile money via TrustChange : plan Créateur activé par la notification.
    fake = FakeTrust(monkeypatch)
    r = await client.post("/billing/checkout", headers=h, json={"product": "creator", "phone": "699000000", "operator": "MTN_CM"})
    ref = r.json()["reference"]
    fake.finish(ref)
    body, sig = fake.webhook(ref)
    assert (await client.post("/billing/webhooks/trust", content=body, headers=sig)).json()["applied"] is True
    me = (await client.get("/me", headers=h)).json()
    assert me["plan"]["id"] == "creator" and me["credits"] == 103

    # Plan Créateur : 6 personnages, 12 pages (scénario en deux passes : 1 plan + 3 lots).
    r = await client.post(f"/series/{sid}/episodes", headers=h, json={"page_count": 12, "character_ids": chars, "direction": "Le bus revient."})
    assert r.status_code == 202
    ep = await wait_done(client, h, r.json()["id"])
    assert ep["status"] == "done", ep["error"]
    script_calls = next(s for s in ep["usage"]["stages"] if s["stage"] == "script")["calls"]
    assert script_calls == 4
    assert ep["usage"]["credits"] == 12 + 3      # 12 pages + 3 nouvelles fiches, pas de couverture
    assert (await client.get("/me", headers=h)).json()["credits"] == 103 - 15

    # Redessin à la demande : 1 crédit, la page reçoit une nouvelle image.
    page = ep["pages"][0]
    r = await client.post(f"/pages/{page['id']}/redraw", headers=h, json={"note": "Le bus a deux volants"})
    assert r.status_code == 202
    for _ in range(100):
        again = (await client.get(f"/episodes/{ep['id']}", headers=h)).json()["pages"][0]
        if again["attempts"] == 2:
            break
        await asyncio.sleep(0.05)
    assert again["url"] != page["url"] and again["editor_note"] == "Le bus a deux volants"
    assert (await client.get("/me", headers=h)).json()["credits"] == 103 - 16

    # Mot bloqué par l'administrateur : refus à la saisie, journalisé.
    await client.post("/admin/terms", headers=h, json={"term": "Décapitation"})
    r = await client.post(f"/series/{sid}/episodes", headers=h, json={"page_count": 4, "character_ids": chars[:2], "direction": "Une d3capitation !"})
    assert r.status_code == 422 and r.json()["detail"]["terms"] == ["decapitation"]
    events = (await client.get("/admin/moderation-events", headers=h)).json()
    assert events[0]["checkpoint"] == "input" and events[0]["action"] == "block"

    # Scène interdite détectée dans le scénario : épisode bloqué, rien dessiné, crédits rendus.
    class StrictChecker(FakeText):
        async def json(self, *, schema_name, **kw):
            if schema_name == "scene_violations":
                return TextResult({"violations": [{"page": 1, "panel": 1, "rule": "nudite-sexe", "reason": "test"}]}, Usage(10, 10))
            return await super().json(schema_name=schema_name, **kw)

    studio = get_studio()
    studio.checker = StrictChecker()
    before = (await client.get("/me", headers=h)).json()["credits"]
    original, runner.get_studio = runner.get_studio, lambda: studio
    try:
        r = await client.post(f"/series/{sid}/episodes", headers=h, json={"page_count": 4, "character_ids": chars[:2]})
        ep = await wait_done(client, h, r.json()["id"])
    finally:
        runner.get_studio = original
    assert ep["status"] == "blocked" and ep["usage"]["images"] == 0 and ep["usage"]["credits"] == 0
    assert (await client.get("/me", headers=h)).json()["credits"] == before
    async with SessionLocal() as s:
        assert (await s.get(Episode, ep["id"])).script is None
