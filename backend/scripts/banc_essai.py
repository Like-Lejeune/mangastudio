"""Banc d'essai : génère un épisode avec les fournisseurs du .env, sans passer par l'interface.

    cd backend && python -m scripts.banc_essai --pages 6 --persos 4

Affiche, pour l'épisode : statut, pages réussies, tokens, images, coût réel et coût
par image livrée. Les images sont dans STORAGE_DIR/series/<id>/ : c'est là qu'on juge
la cohérence des visages et le lettrage en français.
"""
import argparse
import asyncio
import time

from sqlalchemy import func, select

from app import usage
from app.config import get_settings
from app.db import SessionLocal, init_db
from app.models import Character, Episode, EpisodeCharacter, Page, Series, UsageEvent, User, new_id
from app.pipeline.runner import remaining_images, run_episode

PREMISE = "Quatre amis ratent le dernier bus à Yaoundé. Après minuit, la ville change : les rues se déplacent et un bus sans chauffeur les suit."
CAST = [
    ("Awa", "la meneuse", "20 ans, tresses longues attachées, blouson en jean, toujours un carnet à la main"),
    ("Brice", "le rival", "grand et mince, crâne rasé, lunettes rondes, chemise à carreaux ouverte"),
    ("Chantal", "la mécano", "cheveux courts afro, salopette tachée de graisse, clé à molette à la ceinture"),
    ("Didier", "le chauffeur", "la cinquantaine, moustache grise, casquette, uniforme bleu délavé"),
    ("Estelle", "la nouvelle", "petite, foulard jaune, sac à dos trop grand, regard méfiant"),
    ("Francis", "le vendeur de nuit", "trapu, tablier, lampe frontale, plateau d'arachides"),
]


async def main(pages: int, persos: int, palette: str) -> None:
    s = get_settings()
    print(f"Scénariste : {s.writer_provider}/{s.writer_model} · relecteur : {s.checker_provider}/{s.checker_model} · dessin : {s.image_provider}/{s.image_model}")
    await init_db()
    async with SessionLocal() as session:
        user = User(email=f"banc-{new_id()[:8]}@test.local", display_name="Banc d'essai", password_hash="-")
        session.add(user)
        await session.flush()
        series = Series(owner_id=user.id, premise=PREMISE, style="shonen", palette=palette, language="fr")
        session.add(series)
        await session.flush()
        cast = [Character(series_id=series.id, slug=name.lower(), name=name, role=role, description=look) for name, role, look in CAST[:persos]]
        session.add_all(cast)
        episode = Episode(series_id=series.id, number=1, page_count=pages)
        session.add(episode)
        await session.flush()
        session.add_all(EpisodeCharacter(episode_id=episode.id, character_id=c.id) for c in cast)
        await session.flush()
        need = await remaining_images(session, episode)
        await usage.grant(session, user.id, need, "pack", "banc d'essai")
        await usage.reserve(session, user.id, episode.id, need)
        await session.commit()
        episode_id, series_id = episode.id, series.id

    start = time.monotonic()
    await run_episode(episode_id)
    seconds = time.monotonic() - start

    async with SessionLocal() as session:
        episode = await session.get(Episode, episode_id)
        done = (await session.execute(select(func.count()).where(Page.episode_id == episode_id, Page.status == "done"))).scalar_one()
        redrawn = (await session.execute(select(func.count()).where(Page.episode_id == episode_id, Page.attempts > 1))).scalar_one()
        rows = (await session.execute(
            select(UsageEvent.stage, func.count(), func.sum(UsageEvent.input_tokens), func.sum(UsageEvent.output_tokens),
                   func.sum(UsageEvent.images), func.sum(UsageEvent.cost_micro_usd))
            .where(UsageEvent.episode_id == episode_id).group_by(UsageEvent.stage))).all()
        report = await usage.episode_usage(session, episode_id)

    print(f"\nStatut : {episode.status} {episode.error}\nTitre : {episode.title}\nDurée : {seconds:.0f} s · pages réussies : {done}/{pages} · pages redessinées : {redrawn}")
    print(f"\n{'Étape':<12}{'Appels':>7}{'Entrée':>10}{'Sortie':>10}{'Images':>8}{'Coût $':>10}")
    total = 0
    for stage, calls, tin, tout, images, cost in sorted(rows):
        total += cost or 0
        print(f"{stage:<12}{calls:>7}{tin or 0:>10}{tout or 0:>10}{images or 0:>8}{(cost or 0) / 1e6:>10.4f}")
    delivered = report["credits"]
    print(f"\nCoût total : {total / 1e6:.4f} $ · images livrées (crédits) : {delivered}"
          + (f" · coût par crédit : {total / 1e6 / delivered:.4f} $" if delivered else ""))
    print(f"Images : {s.storage_dir}/series/{series_id}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=6)
    parser.add_argument("--persos", type=int, default=4, choices=range(1, 7))
    parser.add_argument("--palette", default="bw", choices=["bw", "color"])
    args = parser.parse_args()
    asyncio.run(main(args.pages, args.persos, args.palette))
