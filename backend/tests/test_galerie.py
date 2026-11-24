"""Galerie « À lire » : demande de publication, validation, likes, classements."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import update

from app.db import SessionLocal
from app.models import Like
from tests.test_admin import account, admin  # noqa: F401  (fixture)
from tests.test_partage import episode_termine


async def test_publication_complete(client, admin):  # noqa: F811
    h, eid = await episode_termine(client, "auteur.galerie@test.cm")
    assert (await client.get(f"/episodes/{eid}/publication", headers=h)).json() is None
    # Sans accepter les règles : refusé.
    r = await client.post(f"/episodes/{eid}/publication", json={"accept_terms": False}, headers=h)
    assert r.status_code == 422 and r.json()["detail"]["code"] == "terms_required"
    r = await client.post(f"/episodes/{eid}/publication", json={"accept_terms": True}, headers=h)
    assert r.json()["status"] == "pending"
    pid = r.json()["id"]
    # En attente : invisible du public.
    assert all(c["id"] != pid for c in (await client.get("/gallery")).json()["items"])
    assert (await client.get(f"/gallery/{pid}")).status_code == 404
    # Un intrus ne peut pas publier l'épisode d'un autre.
    intrus = await account(client, "intrus.galerie@test.cm")
    assert (await client.post(f"/episodes/{eid}/publication", json={"accept_terms": True}, headers=intrus)).status_code == 404
    # Ni un simple compte accéder à la file de l'administration.
    assert (await client.get("/admin/publications", headers=intrus)).status_code == 403

    file = (await client.get("/admin/publications?status=pending", headers=admin)).json()
    assert file["pending"] >= 1 and any(i["id"] == pid for i in file["items"])
    # Refuser exige un motif, montré à l'auteur.
    assert (await client.post(f"/admin/publications/{pid}", json={"action": "reject"}, headers=admin)).status_code == 422
    await client.post(f"/admin/publications/{pid}", json={"action": "reject", "reason": "Texte illisible"}, headers=admin)
    mine = (await client.get(f"/episodes/{eid}/publication", headers=h)).json()
    assert mine["status"] == "rejected" and mine["reason"] == "Texte illisible"
    # L'auteur corrige et redemande ; l'équipe publie.
    await client.post(f"/episodes/{eid}/publication", json={"accept_terms": True}, headers=h)
    await client.post(f"/admin/publications/{pid}", json={"action": "approve"}, headers=admin)
    carte = (await client.get(f"/gallery/{pid}")).json()
    assert carte["author"] == "Awa N." and len(carte["page_urls"]) == 4 and carte["likes"] == 0
    assert "auteur.galerie@test.cm" not in str(carte)                       # jamais l'adresse e-mail
    # Likes : un seul par compte, jamais le sien, annulable.
    assert (await client.post(f"/gallery/{pid}/like", headers=h)).status_code == 409
    assert (await client.post(f"/gallery/{pid}/like")).status_code == 401
    assert (await client.post(f"/gallery/{pid}/like", headers=intrus)).json() == {"likes": 1, "liked": True}
    assert (await client.post(f"/gallery/{pid}/like", headers=intrus)).json() == {"likes": 1, "liked": True}
    assert (await client.get(f"/gallery/{pid}", headers=intrus)).json()["liked"] is True
    assert (await client.delete(f"/gallery/{pid}/like", headers=intrus)).json() == {"likes": 0, "liked": False}
    await client.post(f"/gallery/{pid}/like", headers=intrus)
    # Coup de cœur.
    await client.post(f"/admin/publications/{pid}", json={"action": "feature"}, headers=admin)
    assert any(c["id"] == pid for c in (await client.get("/gallery?tri=coups")).json()["items"])
    # Retrait par l'administration (motif obligatoire) puis par l'auteur.
    await client.post(f"/admin/publications/{pid}", json={"action": "withdraw", "reason": "Signalement"}, headers=admin)
    assert (await client.get(f"/gallery/{pid}")).status_code == 404
    assert all(c["id"] != pid for c in (await client.get("/gallery?tri=coups")).json()["items"])
    journal = (await client.get("/admin/actions", headers=admin)).json()["items"]
    assert any(a["action"] == "publication" and "retirée" in a["detail"] for a in journal)


async def test_episode_non_termine_et_retrait_auteur(client, admin):  # noqa: F811
    h, eid = await episode_termine(client, "auteur2.galerie@test.cm")
    pid = (await client.post(f"/episodes/{eid}/publication", json={"accept_terms": True}, headers=h)).json()["id"]
    await client.post(f"/admin/publications/{pid}", json={"action": "approve"}, headers=admin)
    assert (await client.get(f"/gallery/{pid}")).status_code == 200
    assert (await client.delete(f"/episodes/{eid}/publication", headers=h)).json()["status"] == "withdrawn"
    assert (await client.get(f"/gallery/{pid}")).status_code == 404


async def test_classement_semaine(client, admin):  # noqa: F811
    """« Les plus aimées de la semaine » compte les likes des 7 derniers jours, pas le total."""
    ha, ea = await episode_termine(client, "classe.a@test.cm")
    hb, eb = await episode_termine(client, "classe.b@test.cm")
    pa = (await client.post(f"/episodes/{ea}/publication", json={"accept_terms": True}, headers=ha)).json()["id"]
    pb = (await client.post(f"/episodes/{eb}/publication", json={"accept_terms": True}, headers=hb)).json()["id"]
    for p in (pa, pb):
        await client.post(f"/admin/publications/{p}", json={"action": "approve"}, headers=admin)
    lecteurs = [await account(client, f"lecteur{i}.classe@test.cm") for i in range(3)]
    for h in lecteurs:                       # A : 3 likes, mais anciens
        await client.post(f"/gallery/{pa}/like", headers=h)
    await client.post(f"/gallery/{pb}/like", headers=lecteurs[0])     # B : 1 like récent
    async with SessionLocal() as s:
        await s.execute(update(Like).where(Like.publication_id == pa).values(created_at=datetime.now(timezone.utc) - timedelta(days=10)))
        await s.commit()
    cartes = (await client.get("/gallery?tri=semaine&size=48")).json()["items"]
    semaine = [c["id"] for c in cartes]
    assert semaine.index(pb) < semaine.index(pa)
    assert {c["id"]: c["likes_week"] for c in cartes}[pb] == 1 and {c["id"]: c["likes_week"] for c in cartes}[pa] == 0
    populaires = [c["id"] for c in (await client.get("/gallery?tri=populaires&size=48")).json()["items"]]
    assert populaires.index(pa) < populaires.index(pb)
