"""Personnage refusé par le dessinateur IA : l'auteur est prévenu tôt, l'épisode s'arrête proprement et l'auteur peut continuer."""
from app.pipeline import runner
from app.providers import get_studio
from app.providers.base import ContentBlocked
from app.providers.fake import FakeImage
from tests.test_admin import account, admin  # noqa: F401  (fixture)
from tests.test_flow import wait_done


async def test_nom_protege_refuse_a_la_saisie(client):
    h = await account(client, "protege@test.cm")
    r = await client.post("/series", headers=h, json={"premise": "Sonic le foudroyant veut devenir célèbre."})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "protected_character"
    sid = (await client.post("/series", headers=h, json={"premise": "Un coureur de Douala plus rapide que le son."})).json()["id"]
    r = await client.post(f"/series/{sid}/characters", headers=h, json={"name": "Naruto-kun"})
    assert r.status_code == 422 and "droit d'auteur" in r.json()["detail"]["message"]
    # « Ultrasonic » ou « Mariana » ne sont pas des noms protégés.
    assert (await client.post(f"/series/{sid}/characters", headers=h, json={"name": "Ultrasonic"})).status_code == 201


async def test_fiche_refusee_puis_correction(client, admin):  # noqa: F811
    h = await account(client, "refus.fiche@test.cm")
    sid = (await client.post("/series", headers=h, json={"premise": "Un coureur de Douala plus rapide que le son."})).json()["id"]
    cid = (await client.post(f"/series/{sid}/characters", headers=h, json={"name": "Éclair Bleu", "description": "hérisson bleu"})).json()["id"]
    avant = (await client.get("/me", headers=h)).json()["credits"]

    class Refuse(FakeImage):
        async def draw(self, *, prompt, **kw):
            if "hérisson bleu" in prompt:
                raise ContentBlocked("content_policy_violation")
            return await super().draw(prompt=prompt, **kw)

    studio = get_studio()
    studio.artist = Refuse()
    original, runner.get_studio = runner.get_studio, lambda: studio
    try:
        r = await client.post(f"/series/{sid}/episodes", headers=h, json={"page_count": 4, "character_ids": [cid]})
        ep = await wait_done(client, h, r.json()["id"])
    finally:
        runner.get_studio = original
    # Arrêt propre, message clair, crédits rendus, refus visible dans le journal de modération.
    assert ep["status"] == "blocked" and "« Éclair Bleu »" in ep["error"] and "Modifiez ce personnage" in ep["error"]
    assert (await client.get("/me", headers=h)).json()["credits"] == avant
    detail = (await client.get(f"/admin/episodes/{ep['id']}", headers=admin)).json()
    assert detail["moderation_events"][0]["checkpoint"] == "image"

    # L'auteur modifie son personnage (pas encore dessiné), puis relance : tout passe.
    r = await client.patch(f"/characters/{cid}", headers=h, json={"name": "Éclair", "description": "coureur en survêtement vert"})
    assert r.status_code == 200 and r.json()["name"] == "Éclair"
    assert (await client.patch(f"/characters/{cid}", headers=h, json={"name": "Sonic"})).status_code == 422
    r = await client.post(f"/series/{sid}/episodes", headers=h, json={"page_count": 4, "character_ids": [cid]})
    assert r.status_code == 202
    ep2 = await wait_done(client, h, r.json()["id"])
    assert ep2["status"] == "done" and ep2["number"] == 2
    # Une fois dessiné, le personnage ne se modifie plus.
    assert (await client.patch(f"/characters/{cid}", headers=h, json={"name": "Autre"})).status_code == 409


async def test_abandon_debloque_la_serie(client, admin):  # noqa: F811
    h = await account(client, "abandon@test.cm")
    sid = (await client.post("/series", headers=h, json={"premise": "Une marchande de Mokolo."})).json()["id"]
    cid = (await client.post(f"/series/{sid}/characters", headers=h, json={"name": "Mama Rose"})).json()["id"]

    class Panne(FakeImage):
        async def draw(self, **kw):
            raise RuntimeError("panne")

    studio = get_studio()
    studio.artist = Panne()
    original, runner.get_studio = runner.get_studio, lambda: studio
    try:
        eid = (await client.post(f"/series/{sid}/episodes", headers=h, json={"page_count": 4, "character_ids": [cid]})).json()["id"]
        ep = await wait_done(client, h, eid)
    finally:
        runner.get_studio = original
    assert ep["status"] == "failed"
    r = await client.post(f"/series/{sid}/episodes", headers=h, json={"page_count": 4, "character_ids": [cid]})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "episode_failed"
    # Un autre compte ne peut pas l'abandonner ; l'administration, si.
    intrus = await account(client, "intrus.abandon@test.cm")
    assert (await client.post(f"/episodes/{eid}/abandon", headers=intrus)).status_code == 404
    assert (await client.post(f"/admin/episodes/{eid}/abandon", headers=admin)).json()["status"] == "canceled"
    assert (await client.post(f"/episodes/{eid}/abandon", headers=h)).status_code == 409    # déjà abandonné
    r = await client.post(f"/series/{sid}/episodes", headers=h, json={"page_count": 4, "character_ids": [cid]})
    assert r.status_code == 202
    journal = (await client.get("/admin/actions", headers=admin)).json()["items"]
    assert any(a["action"] == "episode_abandon" for a in journal)
