"""Liste de départ de la modération : 20 textes interdits refusés, textes ordinaires acceptés.

Les textes passent par la vraie route de création de série (point de contrôle n° 1)."""
import pytest
from sqlalchemy import select

from app.db import SessionLocal
from app.models import BlockedTerm, ModerationEvent, SceneRule
from app.moderation_defaults import SCENE_RULES

INTERDITS = [
    "Une histoire porno entre deux collègues de bureau",
    "Un HENTAI au lycée avec des démons",
    "Une scène de sexe explicite dans le dojo",
    "Elle se retrouve toute nue au milieu de la place",
    "Le héros est entièrement nu pendant tout le combat",
    "Une loli qui séduit son professeur",
    "Un manga shotacon dans une école de magie",
    "Le méchant va v-i-o-l-e-r la princesse",
    "Une V1OLÉE dans la forêt maudite",
    "Une romance avec inceste entre frère et sœur",
    "Une scène de z00philie dans la ferme",
    "Un combat très G O R E avec des tripes partout",
    "La décapitation du roi montrée en gros plan",
    "Le démembrement du traître sur la place publique",
    "a NSFW story about a demon hunter",
    "an explicit sex scene in the spaceship",
    "she gets r4ped by the villain",
    "un pédophile dans un club de sport",
    "Le cadavre et la nécrophilie du sorcier",
    "Des seins nus en couverture du chapitre",
]

ACCEPTES = [
    "Une héroïne de Douala découvre qu'elle maîtrise la foudre",
    "Il joue du violon sur l'avenue pendant que l'orage continue",
    "La violence du tournoi pousse les rivaux à s'unir",
    "Un samouraï torse nu s'entraîne sous la cascade",           # « nu » est seulement signalé
    "Le détective enquête sur un trafic de drogue au port",      # « drogue » est seulement signalé
    "Deux lutteurs rivaux du Sussex doivent faire équipe",
]


async def headers(client):
    r = await client.post("/auth/register", json={"email": "moderation@test.cm", "display_name": "Modération", "password": "motdepasse"})
    if r.status_code == 409:
        r = await client.post("/auth/login", json={"email": "moderation@test.cm", "password": "motdepasse"})
    return {"Authorization": f"Bearer {r.json()['token']}"}


async def test_la_liste_initiale_est_chargee(client):
    async with SessionLocal() as s:
        terms = dict((await s.execute(select(BlockedTerm.term, BlockedTerm.action))).all())
        labels = set((await s.execute(select(SceneRule.label))).scalars())
    assert terms.get("porno") == "block" and terms.get("drogue") == "flag"
    assert {label for label, _ in SCENE_RULES} <= labels


@pytest.mark.parametrize("texte", INTERDITS)
async def test_vingt_cas_interdits_sont_refuses(client, texte):
    r = await client.post("/series", json={"premise": texte}, headers=await headers(client))
    assert r.status_code == 422, texte
    assert r.json()["detail"]["code"] == "blocked_terms"


@pytest.mark.parametrize("texte", ACCEPTES)
async def test_textes_ordinaires_acceptes(client, texte):
    r = await client.post("/series", json={"premise": texte}, headers=await headers(client))
    assert r.status_code == 201, (texte, r.text)


async def test_mot_signale_est_journalise(client):
    await client.post("/series", json={"premise": "Un ninja torse nu traverse la ville en courant"}, headers=await headers(client))
    async with SessionLocal() as s:
        ev = (await s.execute(select(ModerationEvent).where(ModerationEvent.rule == "nu", ModerationEvent.action == "flag"))).scalars().first()
    assert ev is not None
