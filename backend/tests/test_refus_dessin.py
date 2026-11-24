"""Personnage refusé par le dessinateur IA : l'auteur est prévenu tôt, l'épisode s'arrête proprement et l'auteur peut continuer."""
from app.pipeline import runner
from app.providers import get_studio
from app.providers.base import ContentBlocked, ProviderError
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


async def test_suppression_episode_abandonne(client, admin):  # noqa: F811
    """Un épisode abandonné s'efface pour de bon : son numéro redevient libre et son histoire n'influence plus la suite."""
    from pathlib import Path

    from sqlalchemy import func, select

    from app.config import get_settings
    from app.db import SessionLocal
    from app.models import Episode, Page, UsageEvent

    h = await account(client, "efface@test.cm")
    sid = (await client.post("/series", headers=h, json={"premise": "Une marchande de Mokolo."})).json()["id"]
    cid = (await client.post(f"/series/{sid}/characters", headers=h, json={"name": "Mama Rose"})).json()["id"]

    class PanneMilieu(FakeImage):
        n = 0

        async def draw(self, **kw):
            PanneMilieu.n += 1
            if PanneMilieu.n > 2:          # fiche et page 1 dessinées, puis panne du fournisseur
                raise ProviderError("panne")
            return await super().draw(**kw)

    studio = get_studio()
    studio.artist = PanneMilieu()
    original, runner.get_studio = runner.get_studio, lambda: studio
    try:
        eid = (await client.post(f"/series/{sid}/episodes", headers=h, json={"page_count": 4, "character_ids": [cid]})).json()["id"]
        ep = await wait_done(client, h, eid)
    finally:
        runner.get_studio = original
    assert ep["status"] == "failed"
    page1 = next(p for p in ep["pages"] if p["url"])
    async with SessionLocal() as s:
        chemin = (await s.execute(select(Page.image_path).where(Page.episode_id == eid, Page.image_path.is_not(None)))).scalar_one()
    fichier = Path(get_settings().storage_dir) / chemin
    assert fichier.exists() and page1["url"]

    # Pas de suppression avant abandon.
    assert (await client.delete(f"/episodes/{eid}", headers=h)).status_code == 409
    await client.post(f"/episodes/{eid}/abandon", headers=h)
    intrus = await account(client, "intrus.efface@test.cm")
    assert (await client.delete(f"/episodes/{eid}", headers=intrus)).status_code == 404
    credits = (await client.get("/me", headers=h)).json()["credits"]
    r = await client.delete(f"/episodes/{eid}", headers=h)
    assert r.json() == {"deleted": True, "series_id": sid}
    assert (await client.get(f"/episodes/{eid}", headers=h)).status_code == 404
    assert not fichier.exists() and not fichier.parent.exists()
    assert (await client.get("/me", headers=h)).json()["credits"] == credits      # rien de rendu ni repris en plus
    async with SessionLocal() as s:
        assert await s.get(Episode, eid) is None
        assert (await s.execute(select(func.count()).select_from(UsageEvent).where(UsageEvent.episode_id == eid))).scalar_one() > 0
    # On repart de zéro : le nouvel épisode reprend le n° 1.
    r = await client.post(f"/series/{sid}/episodes", headers=h, json={"page_count": 4, "character_ids": [cid]})
    ep2 = await wait_done(client, h, r.json()["id"])
    assert ep2["number"] == 1 and ep2["status"] == "done"
    assert all(chemin.split("/")[2] not in p["url"] for p in ep2["pages"])      # nouveau dossier d'images

    # Côté administration : même règle, et l'action est notée.
    await client.post(f"/admin/episodes/{ep2['id']}/abandon", headers=admin)    # refusé : l'épisode est terminé
    assert (await client.delete(f"/admin/episodes/{ep2['id']}", headers=admin)).status_code == 409


async def test_suppression_serie_complete(client, admin):  # noqa: F811
    """Toute une histoire s'efface : personnages, épisodes, images, publication et « j'aime » ; l'historique comptable reste."""
    from pathlib import Path

    from sqlalchemy import func, select

    from app.config import get_settings
    from app.db import SessionLocal
    from app.models import (
        Character,
        Episode,
        Like,
        Page,
        Publication,
        Series,
        UsageEvent,
    )

    h = await account(client, "serie.efface@test.cm")
    sid = (await client.post("/series", headers=h, json={"premise": "Une marchande de Mokolo."})).json()["id"]
    cid = (await client.post(f"/series/{sid}/characters", headers=h, json={"name": "Mama Rose"})).json()["id"]
    eid = (await client.post(f"/series/{sid}/episodes", headers=h, json={"page_count": 4, "character_ids": [cid]})).json()["id"]
    ep = await wait_done(client, h, eid)
    assert ep["status"] == "done"
    pid = (await client.post(f"/episodes/{eid}/publication", headers=h, json={"accept_terms": True})).json()["id"]
    await client.post(f"/admin/publications/{pid}", headers=admin, json={"action": "approve"})
    lecteur = await account(client, "lecteur.serie@test.cm")
    await client.post(f"/gallery/{pid}/like", headers=lecteur)
    dossier = Path(get_settings().storage_dir) / "series" / sid
    assert dossier.exists()
    credits = (await client.get("/me", headers=h)).json()["credits"]

    intrus = await account(client, "intrus.serie@test.cm")
    assert (await client.delete(f"/series/{sid}", headers=intrus)).status_code == 404
    r = await client.delete(f"/series/{sid}", headers=h)
    assert r.status_code == 200 and r.json()["episodes"] == 1
    assert (await client.get(f"/series/{sid}", headers=h)).status_code == 404
    assert (await client.get(f"/gallery/{pid}")).status_code == 404
    assert all(s["id"] != sid for s in (await client.get("/series", headers=h)).json())
    assert not dossier.exists()
    assert (await client.get("/me", headers=h)).json()["credits"] == credits
    async with SessionLocal() as s:
        for model, col, val in ((Series, Series.id, sid), (Character, Character.id, cid), (Episode, Episode.id, eid),
                                (Page, Page.episode_id, eid), (Publication, Publication.id, pid), (Like, Like.publication_id, pid)):
            assert (await s.execute(select(func.count()).select_from(model).where(col == val))).scalar_one() == 0
        assert (await s.execute(select(func.count()).select_from(UsageEvent).where(UsageEvent.episode_id == eid))).scalar_one() > 0


async def test_suppression_serie_admin(client, admin):  # noqa: F811
    h = await account(client, "serie.admin@test.cm")
    sid = (await client.post("/series", headers=h, json={"premise": "Un griot de Garoua."})).json()["id"]
    await client.post(f"/series/{sid}/characters", headers=h, json={"name": "Baba"})
    assert (await client.delete(f"/admin/series/{sid}", headers=h)).status_code == 403
    assert (await client.delete(f"/admin/series/{sid}", headers=admin)).json()["deleted"] is True
    assert (await client.get(f"/series/{sid}", headers=h)).status_code == 404
    journal = (await client.get("/admin/actions", headers=admin)).json()["items"]
    assert any(a["action"] == "series_delete" for a in journal)
