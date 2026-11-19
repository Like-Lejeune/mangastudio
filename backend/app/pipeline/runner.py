"""Génération d'un épisode, de bout en bout, en tâche de fond.

Chaque étape enregistre son résultat : relancer run_episode() sur un épisode
interrompu reprend où il s'est arrêté (design, scénario, fiches, pages déjà
faits sont sautés). Les crédits réservés au lancement sont réglés à la fin :
seules les images livrées sont débitées."""
import asyncio
import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import moderation, storage, usage
from app.config import get_settings
from app.db import SessionLocal
from app.models import Character, Episode, EpisodeCharacter, Page, Series, UsageEvent
from app.pipeline import prompts
from app.pipeline.script import (ScriptIncomplete, batch_schema, normalise_pages, outline_schema, script_schema, script_text)
from app.providers import Studio, get_studio
from app.providers.base import ContentBlocked, ProviderError, Usage

log = logging.getLogger("pipeline")
MIME = {"png": "image/png", "jpg": "image/jpeg", "webp": "image/webp", "svg": "image/svg+xml"}


class Blocked(Exception):
    """La modération a arrêté l'épisode."""


def _mime(path: str) -> str:
    return MIME.get(path.rsplit(".", 1)[-1], "image/png")


async def _load(session: AsyncSession, episode_id: str) -> Episode | None:
    return (await session.execute(
        select(Episode).where(Episode.id == episode_id).options(
            selectinload(Episode.series), selectinload(Episode.pages),
            selectinload(Episode.cast).selectinload(EpisodeCharacter.character),
        )
    )).scalar_one_or_none()


async def delivered_images(session: AsyncSession, episode_id: str) -> int:
    """Images livrées et donc facturées : pages réussies, fiches, couverture, redessins demandés."""
    pages = (await session.execute(select(func.count()).where(Page.episode_id == episode_id, Page.status == "done"))).scalar_one()
    others = (await session.execute(
        select(func.count()).where(UsageEvent.episode_id == episode_id, UsageEvent.stage.in_(("sheet", "cover", "redraw")))
    )).scalar_one()
    return pages + others


async def remaining_images(session: AsyncSession, episode: Episode) -> int:
    """Pire cas de ce qu'il reste à dessiner : sert à calculer la réserve de crédits."""
    await session.refresh(episode, ["pages", "cast", "series"])
    done = sum(1 for p in episode.pages if p.status == "done")
    cast_ids = [ec.character_id for ec in episode.cast]
    sheets = (await session.execute(
        select(func.count()).where(Character.id.in_(cast_ids), Character.sheet_path.is_(None))
    )).scalar_one() if cast_ids else 0
    cover = 0 if episode.series.cover_path else 1
    return (episode.page_count - done) + sheets + cover


async def run_episode(episode_id: str, studio: Studio | None = None) -> None:
    studio = studio or get_studio()
    async with SessionLocal() as session:
        episode = await _load(session, episode_id)
        if episode is None or episode.status == "done":
            return
        user_id = episode.series.owner_id
        status, error = "done", ""
        try:
            await _run(session, episode, studio, user_id)
            failed = [p.number for p in episode.pages if p.status != "done"]
            if failed:
                status, error = "failed", f"Pages à refaire : {', '.join(map(str, failed))}."
        except Blocked as e:
            status, error = "blocked", str(e)
        except Exception as e:  # noqa: BLE001  (toute panne doit laisser l'épisode dans un état lisible)
            log.exception("épisode %s", episode_id)
            status, error = "failed", f"La génération s'est interrompue ({type(e).__name__}). Vous pouvez la reprendre."
        # Clôture dans une transaction propre : statut, puis remboursement de la réserve non utilisée.
        await session.rollback()
        episode = await session.get(Episode, episode_id)
        episode.status, episode.error = status, error
        await usage.settle(session, user_id, episode_id, await delivered_images(session, episode_id))
        await session.commit()


async def _run(session: AsyncSession, episode: Episode, studio: Studio, user_id: str) -> None:
    series: Series = episode.series
    cast: list[Character] = [ec.character for ec in episode.cast]

    def record(stage: str, provider, model: str, used) -> None:
        usage.record(session, user_id=user_id, episode_id=episode.id, stage=stage, provider=provider.name, model=model, usage=used)

    # 1. Design : chaque nouveau personnage reçoit une description fixe, dessinable.
    episode.status = "designing"
    await session.commit()
    for c in cast:
        if c.look:
            continue
        if c.photo_path:
            photo = await storage.load(c.photo_path)
            res = await studio.checker.json(
                model=studio.checker_model, system=prompts.DESIGN_SYSTEM,
                user=prompts.design_user(c.name, c.description, series.style, series.palette, series.premise),
                schema=prompts.LOOK_SCHEMA, schema_name="character_design",
                images=[(photo, _mime(c.photo_path))], max_tokens=2000,
            )
            record("design", studio.checker, studio.checker_model, res.usage)
            c.look = str(res.data.get("look", ""))[:900] or c.description or c.name
        else:
            c.look = c.description or c.name
    await session.commit()

    # 2 et 3. Scénario, puis modération : rien n'est dessiné avant ce feu vert.
    if episode.script is None:
        episode.status = "writing"
        await session.commit()
        fix = ""
        for attempt in range(2):
            script = await _write_script(session, episode, series, cast, studio, record, fix)
            episode.status = "moderating"
            await session.commit()
            problems = await _moderate(session, episode, script, studio, record, user_id)
            if not problems:
                break
            if attempt == 1:
                await session.commit()   # garde le journal de modération
                raise Blocked("Le scénario contient une scène ou un mot non autorisé : " + " ; ".join(problems))
            fix = "\n".join(f"- {p}" for p in problems)
        episode.script = script
        episode.title, episode.summary = script["episode_title"][:120], script["summary"]
        series.title = series.title or script["title"][:120]
        series.setting = series.setting or script["setting"]
        existing = {p.number for p in episode.pages}
        for n in range(1, episode.page_count + 1):
            if n not in existing:
                session.add(Page(episode_id=episode.id, number=n))
        await session.commit()
        await session.refresh(episode, ["pages"])
    script = episode.script

    # 4. Fiches modèles des nouveaux personnages (en parallèle).
    episode.status = "drawing"
    await session.commit()
    sem = asyncio.Semaphore(get_settings().page_concurrency)

    async def sheet(c: Character):
        refs = [(await storage.load(c.photo_path), _mime(c.photo_path))] if c.photo_path else []
        info = {"name": c.name, "look": c.look}
        async with sem:
            return c, await _draw(studio, prompts.sheet_prompt(info, series.style, series.palette, bool(refs)), refs, "1536x1024")

    for c, result in await asyncio.gather(*(sheet(c) for c in cast if not c.sheet_path)):
        c.sheet_path = await storage.save(f"series/{series.id}/sheets/{c.slug}", result.image, result.mime)
        record("sheet", studio.artist, studio.artist_model, result.usage)
    await session.commit()

    sheets = {c.slug: (await storage.load(c.sheet_path), _mime(c.sheet_path)) for c in cast}
    names = {c.slug: c.name for c in cast}
    rules = moderation.rules_text(await moderation.scene_rules(session))
    lock = asyncio.Lock()   # une seule écriture en base à la fois ; les appels aux modèles restent parallèles

    # 5. Pages : dessin, relecture, un redessin au plus. Chaque page est enregistrée dès qu'elle est prête.
    async def page(row: Page) -> None:
        spec = script["pages"][row.number - 1]
        order = list(dict.fromkeys(s for p in spec["panels"] for s in p["characters"])) or list(sheets)
        order = order[: studio.max_refs]
        refs = [sheets[s] for s in order]
        events, image, note, attempts, forbidden = [], None, "", 0, False

        def build(fix: str = "") -> str:
            return prompts.page_prompt(script, spec, names, order, series.style, series.palette, series.language, fix)

        async with sem:
            try:
                image = await _draw(studio, build(), refs)
                attempts = 1
                events.append(("page", studio.artist, studio.artist_model, image.usage))
                verdict, used = await _check(studio, image, refs, build(), series.palette, rules)
                events.append(("check", studio.checker, studio.checker_model, used))
                if not verdict["pass"] and verdict["fix"]:
                    note, forbidden = verdict["fix"], bool(verdict["rule"])
                    try:
                        image = await _draw(studio, build(verdict["fix"]), refs)
                        attempts = 2
                        events.append(("page", studio.artist, studio.artist_model, image.usage))
                        if forbidden:   # scène interdite : on vérifie que le redessin l'a retirée
                            verdict, used = await _check(studio, image, refs, build(), series.palette, rules)
                            events.append(("check", studio.checker, studio.checker_model, used))
                            forbidden = bool(verdict["rule"])
                    except (ContentBlocked, ProviderError):
                        pass   # le redessin a échoué : on garde le premier dessin, sauf scène interdite
            except (ContentBlocked, ProviderError) as e:
                image, note = None, f"Dessin impossible ({type(e).__name__})."
        async with lock:
            if image and not forbidden:
                row.image_path = await storage.save(f"series/{series.id}/ep{episode.number}/page-{row.number}", image.image, image.mime)
                row.status = "done"
            else:
                row.status = "failed"
            if forbidden:
                moderation.log(session, user_id=user_id, episode_id=episode.id, checkpoint="image", action="block", rule="scène interdite", excerpt=note)
            row.attempts += attempts
            row.editor_note = note
            for stage, provider, model, used in events:
                record(stage, provider, model, used)
            await session.commit()

    await asyncio.gather(*(page(row) for row in episode.pages if row.status != "done"))

    # 6. Couverture, une fois par série.
    if not series.cover_path:
        order = list(sheets)[: studio.max_refs]
        try:
            cover = await _draw(studio, prompts.cover_prompt(series.title, series.setting, [names[s] for s in order], series.style, series.palette), [sheets[s] for s in order])
            series.cover_path = await storage.save(f"series/{series.id}/cover", cover.image, cover.mime)
            record("cover", studio.artist, studio.artist_model, cover.usage)
        except (ContentBlocked, ProviderError):
            log.warning("couverture non dessinée pour la série %s", series.id)
        await session.commit()


async def _write_script(session, episode: Episode, series: Series, cast: list[Character], studio: Studio, record, fix: str) -> dict:
    """Un appel jusqu'à `single_pass_max_pages` pages ; au-delà, le plan puis des lots de pages."""
    cfg = get_settings()
    slugs = [c.slug for c in cast]
    max_per_page = max(1, min(studio.max_refs, len(slugs)))
    previous = (await session.execute(
        select(Episode.number, Episode.title, Episode.summary)
        .where(Episode.series_id == series.id, Episode.number < episode.number, Episode.script.is_not(None))
        .order_by(Episode.number.desc()).limit(8)
    )).all()
    context = prompts.story_context(
        {"premise": series.premise, "title": series.title, "setting": series.setting, "style": series.style},
        [{"slug": c.slug, "name": c.name, "role": c.role, "look": c.look} for c in cast],
        [{"number": n, "title": t, "summary": s} for n, t, s in reversed(previous)],
        episode.direction, episode.number, episode.page_count, max_per_page,
    )
    system = prompts.writer_system(series.language)
    n = episode.page_count

    async def ask(user: str, schema: dict, name: str) -> dict:
        res = await studio.writer.json(model=studio.writer_model, system=system, user=user, schema=schema, schema_name=name)
        record("script", studio.writer, studio.writer_model, res.usage)
        return res.data

    for attempt in range(2):   # un scénario incomplet a droit à un second essai
        try:
            if n <= cfg.single_pass_max_pages:
                raw = await ask(prompts.writer_single(context, n, fix), script_schema(n, slugs), "episode_script")
                pages = normalise_pages(raw.get("pages") or [], n, slugs, max_per_page)
            else:
                raw = await ask(prompts.writer_outline(context, n, fix), outline_schema(n), "episode_outline")
                beats = [str(b) for b in (raw.get("beats") or [])][:n]
                if len(beats) < n:
                    raise ScriptIncomplete("plan incomplet")
                pages, written = [], []
                for first in range(1, n + 1, cfg.script_batch_size):
                    count = min(cfg.script_batch_size, n - first + 1)
                    batch = await ask(prompts.writer_batch(context, beats, first, first + count - 1, written), batch_schema(count, slugs), "episode_pages")
                    part = normalise_pages(batch.get("pages") or [], count, slugs, max_per_page, first)
                    pages += part
                    written += [f"Page {p['number']}: {p['beat']}" for p in part]
            return {
                "title": str(raw.get("title") or series.title or "Sans titre"),
                "episode_title": str(raw.get("episode_title") or f"Épisode {episode.number}"),
                "tagline": str(raw.get("tagline") or ""),
                "setting": series.setting or str(raw.get("setting") or ""),
                "summary": str(raw.get("summary") or ""),
                "pages": pages,
            }
        except ScriptIncomplete:
            if attempt == 1:
                raise
    raise ScriptIncomplete("scénario incomplet")


async def _moderate(session, episode: Episode, script: dict, studio: Studio, record, user_id: str) -> list[str]:
    """Point de contrôle n° 2. Renvoie la liste des problèmes (vide = feu vert)."""
    problems = []
    verdict = await moderation.check_text(session, script_text(script))
    for term in verdict.flagged:
        moderation.log(session, user_id=user_id, episode_id=episode.id, checkpoint="script", action="flag", rule=term)
    for term in verdict.blocked:
        moderation.log(session, user_id=user_id, episode_id=episode.id, checkpoint="script", action="block", rule=term)
        problems.append(f"mot interdit « {term} »")
    rules = await moderation.scene_rules(session)
    violations, used = await moderation.classify_script(studio.checker, studio.checker_model, script, rules)
    record("moderation", studio.checker, studio.checker_model, used)
    for v in violations:
        moderation.log(session, user_id=user_id, episode_id=episode.id, checkpoint="script", action="block", rule=v["rule"], excerpt=v.get("reason", ""))
        problems.append(f"page {v.get('page')}, case {v.get('panel')} : {v['rule']} ({v.get('reason', '')})")
    return problems


async def _draw(studio: Studio, prompt: str, refs: list, size: str = "1024x1536"):
    """Un dessin ; si le filtre du fournisseur refuse, un second essai adouci."""
    try:
        return await studio.artist.draw(model=studio.artist_model, prompt=prompt, references=refs, size=size)
    except ContentBlocked:
        return await studio.artist.draw(model=studio.artist_model, prompt=f"{prompt}\n{prompts.SOFTEN}", references=refs, size=size)


async def _check(studio: Studio, image, refs: list, brief: str, palette: str, rules: str):
    """Relecture d'une page. Une relecture en panne ne bloque jamais la page."""
    try:
        res = await studio.checker.json(
            model=studio.checker_model, system=prompts.editor_system(palette, rules),
            user=f"Script of the page:\n{brief}\n\nFirst image: the page. Then the model sheets, in order.",
            schema=prompts.CHECK_SCHEMA, schema_name="page_check",
            images=[(image.image, image.mime), *refs], max_tokens=2000,
        )
        d = res.data
        return {"pass": bool(d.get("pass")), "fix": str(d.get("fix") or ""), "rule": str(d.get("rule") or "")}, res.usage
    except ProviderError:
        return {"pass": True, "fix": "", "rule": ""}, Usage()


async def redraw_page(page_id: str, note: str, studio: Studio | None = None) -> None:
    """Redessin demandé par l'utilisateur, avec sa remarque. Facturé 1 crédit (étape « redraw »)."""
    studio = studio or get_studio()
    async with SessionLocal() as session:
        row = await session.get(Page, page_id)
        episode = await _load(session, row.episode_id)
        series, script = episode.series, episode.script
        cast = [ec.character for ec in episode.cast]
        names = {c.slug: c.name for c in cast}
        spec = script["pages"][row.number - 1]
        order = (list(dict.fromkeys(s for p in spec["panels"] for s in p["characters"])) or list(names))[: studio.max_refs]
        refs = [(await storage.load(c.sheet_path), _mime(c.sheet_path)) for slug in order for c in cast if c.slug == slug and c.sheet_path]
        try:
            image = await _draw(studio, prompts.page_prompt(script, spec, names, order, series.style, series.palette, series.language, note[:300]), refs)
            row.image_path = await storage.save(f"series/{series.id}/ep{episode.number}/page-{row.number}-r{row.attempts + 1}", image.image, image.mime)
            was_done = row.status == "done"
            row.status, row.attempts, row.editor_note = "done", row.attempts + 1, note[:300]
            # Page déjà livrée : le redessin compte comme une image de plus ; page ratée : il devient la page livrée.
            usage.record(session, user_id=series.owner_id, episode_id=episode.id, stage="redraw" if was_done else "page",
                         provider=studio.artist.name, model=studio.artist_model, usage=image.usage)
            await session.commit()
        except (ContentBlocked, ProviderError):
            log.warning("redessin impossible pour la page %s", page_id)
            await session.rollback()
            row = await session.get(Page, page_id)
            row.attempts, row.editor_note = row.attempts + 1, "Redessin impossible, crédit rendu."
        # Dans tous les cas : le crédit réservé est rendu si aucune image n'a été livrée.
        await usage.settle(session, series.owner_id, episode.id, await delivered_images(session, episode.id))
        await session.commit()
