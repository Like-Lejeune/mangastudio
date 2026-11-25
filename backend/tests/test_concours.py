"""Concours : création, inscription, « j'aime » pendant le concours, jury, proclamation et lots."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import update

from app import contests as C
from app.db import SessionLocal
from app.models import Contest, Episode
from tests.test_admin import account, admin  # noqa: F401  (fixture)
from tests.test_partage import episode_termine


def _dates(debut_h=-1, fin_h=24):
    t = datetime.now(timezone.utc)
    return (t + timedelta(hours=debut_h)).isoformat(), (t + timedelta(hours=fin_h)).isoformat()


async def _concours(client, admin, **extra):  # noqa: F811
    debut, fin = _dates()
    body = {"title": "Contes et légendes d'Afrique", "theme": "Un conte revisité", "rules": "Règlement de test",
            "starts_at": debut, "ends_at": fin, "visible": True,
            "prizes": [{"rank": 1, "credits": 100, "studio_days": 30}, {"rank": 2, "credits": 50}]} | extra
    r = await client.post("/admin/contests", headers=admin, json=body)
    assert r.status_code == 201, r.text
    return r.json()


async def _publie(client, admin, email):  # noqa: F811
    h, eid = await episode_termine(client, email)
    pid = (await client.post(f"/episodes/{eid}/publication", headers=h, json={"accept_terms": True})).json()["id"]
    return h, eid, pid


def test_score():
    assert C.score(10, 2, 2) == 14.0           # 0,6 × 10 + 0,4 × 20
    assert C.score(16, 1, 2) == 13.6           # 0,6 × 16 + 0,4 × 10
    assert C.score(12, 0, 0) == 7.2            # aucun « j'aime » dans tout le concours
    assert C.slugify("Contes et légendes d'Afrique !") == "contes-et-legendes-d-afrique"


async def test_brouillon_invisible_et_validations(client, admin):  # noqa: F811
    debut, fin = _dates()
    r = await client.post("/admin/contests", headers=admin, json={"title": "Brouillon", "starts_at": debut, "ends_at": fin})
    c = r.json()
    assert c["visible"] is False and c["phase"] == "en_cours"
    assert (await client.get(f"/contests/{c['slug']}")).status_code == 404
    assert all(x["id"] != c["id"] for x in (await client.get("/contests")).json()["items"])
    # Clôture avant ouverture, lots en double, style inconnu : refusés.
    assert (await client.post("/admin/contests", headers=admin, json={"title": "Faux", "starts_at": fin, "ends_at": debut})).status_code == 422
    assert (await client.post("/admin/contests", headers=admin, json={"title": "Faux", "starts_at": debut, "ends_at": fin,
            "prizes": [{"rank": 1, "credits": 5}, {"rank": 1, "credits": 9}]})).status_code == 422
    assert (await client.post("/admin/contests", headers=admin, json={"title": "Faux", "starts_at": debut, "ends_at": fin, "style": "xyz"})).status_code == 422
    # Réservé à l'administration ; un deuxième concours du même titre reçoit une autre adresse.
    h = await account(client, "curieux.concours@test.cm")
    assert (await client.post("/admin/contests", headers=h, json={"title": "X", "starts_at": debut, "ends_at": fin})).status_code == 403
    autre = (await client.post("/admin/contests", headers=admin, json={"title": "Brouillon", "starts_at": debut, "ends_at": fin})).json()
    assert autre["slug"] != c["slug"]


async def test_concours_complet(client, admin):  # noqa: F811
    c = await _concours(client, admin)
    slug = c["slug"]
    ha, ea, pa = await _publie(client, admin, "concours.a@test.cm")
    hb, eb, pb = await _publie(client, admin, "concours.b@test.cm")

    # Le chapitre de A est encore en relecture : il peut s'inscrire, mais n'apparaît qu'une fois publié.
    page = (await client.get(f"/contests/{slug}", headers=ha)).json()
    assert page["phase"] == "en_cours" and [e["publication_id"] for e in page["eligible"]] == [pa] and page["eligible"][0]["ok"]
    assert (await client.post(f"/contests/{slug}/entries", headers=ha, json={"publication_id": pa})).status_code == 201
    assert (await client.get(f"/contests/{slug}")).json()["entries_list"] == []
    # Une seule histoire par participant, jamais celle d'un autre.
    assert (await client.post(f"/contests/{slug}/entries", headers=ha, json={"publication_id": pa})).status_code == 409
    assert (await client.post(f"/contests/{slug}/entries", headers=ha, json={"publication_id": pb})).status_code == 404
    assert (await client.post(f"/contests/{slug}/entries", headers=hb, json={"publication_id": pb})).status_code == 201
    for p in (pa, pb):
        await client.post(f"/admin/publications/{p}", headers=admin, json={"action": "approve"})

    # « J'aime » : 2 pour A, 1 pour B pendant le concours ; un « j'aime » ancien sur B ne compte pas.
    lecteurs = [await account(client, f"lecteur{i}.concours@test.cm") for i in range(3)]
    await client.post(f"/gallery/{pa}/like", headers=lecteurs[0])
    await client.post(f"/gallery/{pa}/like", headers=lecteurs[1])
    await client.post(f"/gallery/{pb}/like", headers=lecteurs[0])
    await client.post(f"/gallery/{pb}/like", headers=lecteurs[2])
    from app.models import Like
    async with SessionLocal() as s:
        await s.execute(update(Like).where(Like.publication_id == pb, Like.user_id.in_(
            [u for u in [await _uid(client, lecteurs[2])]])).values(created_at=datetime.now(timezone.utc) - timedelta(days=3)))
        await s.commit()
    public = (await client.get(f"/contests/{slug}")).json()
    assert {e["id"]: e["contest_likes"] for e in public["entries_list"]} == {pa: 2, pb: 1}
    assert all(e["jury_score"] is None for e in public["entries_list"])        # notes du jury secrètes avant proclamation

    # Pas de proclamation pendant le concours.
    assert (await client.post(f"/admin/contests/{c['id']}/results", headers=admin)).status_code == 409
    # Clôture : plus d'inscription ni de retrait.
    async with SessionLocal() as s:
        # Les « j'aime » du concours datent d'il y a 10 min ; on clôt il y a 1 min.
        await s.execute(update(Like).where(Like.publication_id.in_([pa, pb]), Like.created_at > datetime.now(timezone.utc) - timedelta(days=1))
                        .values(created_at=datetime.now(timezone.utc) - timedelta(minutes=10)))
        await s.execute(update(Contest).where(Contest.id == c["id"]).values(ends_at=datetime.now(timezone.utc) - timedelta(minutes=1)))
        await s.commit()
    assert (await client.get(f"/contests/{slug}")).json()["phase"] == "deliberation"
    eb_entry = next(e["entry_id"] for e in public["entries_list"] if e["id"] == pb)
    assert (await client.delete(f"/contests/{slug}/entries/{eb_entry}", headers=hb)).status_code == 409

    # Le jury doit avoir tout noté.
    detail = (await client.get(f"/admin/contests/{c['id']}", headers=admin)).json()
    ids = {e["id"]: e["entry_id"] for e in detail["entries_list"]}
    await client.post(f"/admin/contests/{c['id']}/entries/{ids[pa]}", headers=admin, json={"jury_score": 10})
    r = await client.post(f"/admin/contests/{c['id']}/results", headers=admin)
    assert r.status_code == 409 and "1 histoire" in r.json()["detail"]
    await client.post(f"/admin/contests/{c['id']}/entries/{ids[pb]}", headers=admin, json={"jury_score": 16})

    avant_a = (await client.get("/me", headers=ha)).json()["credits"]
    avant_b = (await client.get("/me", headers=hb)).json()["credits"]
    assert (await client.post(f"/admin/contests/{c['id']}/results", headers=admin)).json()["ranked"] == 2
    res = (await client.get(f"/contests/{slug}")).json()
    assert res["phase"] == "termine"
    classement = [(e["id"], e["rank"], e["score"], e["contest_likes"]) for e in res["entries_list"]]
    assert classement == [(pa, 1, 14.0, 2), (pb, 2, 13.6, 1)]
    # Lots : crédits, et 30 jours de plan Studio pour le premier.
    me_a = (await client.get("/me", headers=ha)).json()
    assert me_a["credits"] == avant_a + 100 and me_a["plan"]["id"] == "studio"
    assert (await client.get("/me", headers=hb)).json()["credits"] == avant_b + 50
    # Prix affiché sur la page de lecture, résultats figés, une seule proclamation.
    assert (await client.get(f"/gallery/{pa}")).json()["awards"][0]["label"].startswith("1er prix")
    assert (await client.post(f"/admin/contests/{c['id']}/results", headers=admin)).status_code == 409
    assert (await client.put(f"/admin/contests/{c['id']}", headers=admin, json={"title": "Autre titre", "starts_at": _dates()[0], "ends_at": _dates()[1]})).status_code == 409
    journal = (await client.get("/admin/actions", headers=admin)).json()["items"]
    assert any(a["action"] == "contest_results" and "1er prix" in a["detail"] for a in journal)
    stats = (await client.get("/admin/overview", headers=admin)).json()["free_credits"]["by_source"]
    assert stats["Concours"] >= 150


async def _uid(client, h):
    return (await client.get("/me", headers=h)).json()["id"]


async def test_regles_d_inscription(client, admin):  # noqa: F811
    # Style imposé : un chapitre d'un autre style est refusé, avec la raison.
    c = await _concours(client, admin, title="Spécial afro", style="afro")
    h, eid, pid = await _publie(client, admin, "style.concours@test.cm")
    page = (await client.get(f"/contests/{c['slug']}", headers=h)).json()
    assert page["eligible"][0]["ok"] is False and "style" in page["eligible"][0]["why"]
    assert (await client.post(f"/contests/{c['slug']}/entries", headers=h, json={"publication_id": pid})).status_code == 409
    # Chapitre créé avant l'ouverture : refusé quand le concours n'accepte que des nouveautés.
    c2 = await _concours(client, admin, title="Nouveautés seulement")
    async with SessionLocal() as s:
        await s.execute(update(Episode).where(Episode.id == eid).values(created_at=datetime.now(timezone.utc) - timedelta(days=2)))
        await s.commit()
    r = await client.post(f"/contests/{c2['slug']}/entries", headers=h, json={"publication_id": pid})
    assert r.status_code == 409 and "depuis son ouverture" in r.json()["detail"]
    # Concours qui accepte les anciens chapitres, à deux histoires par personne : retrait possible pendant le concours.
    c3 = await _concours(client, admin, title="Ouvert à tous", new_only=False, max_entries=2)
    en = (await client.post(f"/contests/{c3['slug']}/entries", headers=h, json={"publication_id": pid})).json()["entry_id"]
    assert (await client.delete(f"/contests/{c3['slug']}/entries/{en}", headers=h)).json() == {"ok": True}
    # Pas encore ouvert : inscription refusée.
    debut, fin = _dates(24, 48)
    c4 = await _concours(client, admin, title="Plus tard", starts_at=debut, ends_at=fin)
    assert (await client.get(f"/contests/{c4['slug']}")).json()["phase"] == "a_venir"
    assert (await client.post(f"/contests/{c4['slug']}/entries", headers=h, json={"publication_id": pid})).status_code == 409


async def test_disqualification_et_suppression(client, admin):  # noqa: F811
    c = await _concours(client, admin, title="Avec disqualification")
    h, eid, pid = await _publie(client, admin, "disq.concours@test.cm")
    await client.post(f"/admin/publications/{pid}", headers=admin, json={"action": "approve"})
    en = (await client.post(f"/contests/{c['slug']}/entries", headers=h, json={"publication_id": pid})).json()["entry_id"]
    await client.post(f"/admin/contests/{c['id']}/entries/{en}", headers=admin, json={"disqualified": "Personnage existant"})
    assert (await client.get(f"/contests/{c['slug']}")).json()["entries_list"] == []
    mine = (await client.get(f"/contests/{c['slug']}", headers=h)).json()["mine"]
    assert mine[0]["disqualified"] == "Personnage existant"
    # Supprimer la série retire aussi l'inscription.
    sid = (await client.get(f"/episodes/{eid}", headers=h)).json()["series_id"]
    assert (await client.delete(f"/series/{sid}", headers=h)).status_code == 200
    assert (await client.get(f"/admin/contests/{c['id']}", headers=admin)).json()["entries_list"] == []
