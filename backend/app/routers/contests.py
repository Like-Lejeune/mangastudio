"""Concours : pages publiques, inscription des auteurs, jury et proclamation par l'administration."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import contests as C
from app.db import get_session
from app.i18n import lang, tr
from app.models import Contest, ContestEntry, Episode, Publication, User
from app.pipeline.prompts import STYLES
from app.routers.admin_ops import iso, log
from app.routers.gallery import _card, _liked_ids
from app.security import admin_user, optional_user, verified_user
from app.services import aware

router = APIRouter(tags=["concours"])


def contest_out(c: Contest, entries: int = 0, *, admin: bool = False) -> dict:
    """Public : en anglais, la version anglaise remplace chaque texte quand elle est remplie.
    Administration : les deux versions telles qu'enregistrées, pour le formulaire."""
    en = not admin and lang() == "en"
    pick = (lambda fr, eng: eng if en and eng.strip() else fr)
    data = {
        "id": c.id, "slug": c.slug, "title": pick(c.title, c.title_en), "theme": pick(c.theme, c.theme_en),
        "description": pick(c.description, c.description_en), "rules": pick(c.rules, c.rules_en),
        "style": c.style, "new_only": c.new_only, "max_entries": c.max_entries,
        "prizes": [{**p, "label": C.prize_label(p, "en" if en else "fr")} for p in sorted(c.prizes or [], key=lambda p: p.get("rank", 99))],
        "starts_at": iso(c.starts_at), "ends_at": iso(c.ends_at), "results_at": iso(c.results_at),
        "visible": c.visible, "phase": C.phase(c), "phase_label": (C.PHASES_EN if en else C.PHASES)[C.phase(c)], "entries": entries,
    }
    if admin:
        data.update({"title_en": c.title_en, "theme_en": c.theme_en, "description_en": c.description_en, "rules_en": c.rules_en})
    return data


async def _counts(session: AsyncSession, ids: list[str]) -> dict[str, int]:
    if not ids:
        return {}
    rows = (await session.execute(
        select(ContestEntry.contest_id, func.count()).join(Publication, Publication.id == ContestEntry.publication_id)
        .where(ContestEntry.contest_id.in_(ids), ContestEntry.disqualified == "", Publication.status == "published")
        .group_by(ContestEntry.contest_id))).all()
    return {cid: int(n) for cid, n in rows}


async def _visible(session: AsyncSession, slug: str) -> Contest:
    c = (await session.execute(select(Contest).where(Contest.slug == slug, Contest.visible.is_(True)))).scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Concours introuvable.")
    return c


async def _entries_view(session: AsyncSession, c: Contest, user: User | None, *, admin: bool = False) -> list[dict]:
    q = (select(ContestEntry, Publication, Episode, User.display_name, User.email)
         .join(Publication, Publication.id == ContestEntry.publication_id)
         .join(Episode, Episode.id == Publication.episode_id).join(User, User.id == ContestEntry.user_id)
         .where(ContestEntry.contest_id == c.id)
         .options(selectinload(Episode.pages), selectinload(Episode.series)))
    if not admin:
        q = q.where(ContestEntry.disqualified == "", Publication.status == "published")
    rows = (await session.execute(q)).all()
    live = await C.contest_likes(session, c, [p.id for _, p, _, _, _ in rows]) if not c.results_at else {}
    liked = await _liked_ids(session, user, [p.id for _, p, _, _, _ in rows])
    out = []
    for en, p, e, author, email in rows:
        d = _card(p, e, author, p.id in liked)
        d.update({"entry_id": en.id, "contest_likes": en.likes if c.results_at else live.get(p.id, 0),
                  "rank": en.rank, "score": en.score, "prize": en.prize, "jury_score": en.jury_score if c.results_at or admin else None})
        if admin:
            d.update({"email": email, "user_id": en.user_id, "publication_status": p.status, "disqualified": en.disqualified,
                      "entered_at": iso(en.created_at)})
        out.append(d)
    if c.results_at:
        out.sort(key=lambda d: (d["rank"] is None, d["rank"] or 0))
    else:
        out.sort(key=lambda d: -d["contest_likes"])
    return out


# ---------- Public ----------

@router.get("/contests")
async def list_contests(session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(Contest).where(Contest.visible.is_(True)).order_by(Contest.starts_at.desc()))).scalars().all()
    counts = await _counts(session, [c.id for c in rows])
    order = {"en_cours": 0, "a_venir": 1, "deliberation": 2, "termine": 3}
    items = sorted((contest_out(c, counts.get(c.id, 0)) for c in rows), key=lambda d: order[d["phase"]])
    return {"items": items}


@router.get("/contests/{slug}")
async def get_contest(slug: str, user: User | None = Depends(optional_user), session: AsyncSession = Depends(get_session)):
    c = await _visible(session, slug)
    entries = await _entries_view(session, c, user)
    data = contest_out(c, len(entries))
    data["entries_list"] = entries
    if user:
        mine = (await session.execute(
            select(ContestEntry, Publication.status).join(Publication, Publication.id == ContestEntry.publication_id)
            .where(ContestEntry.contest_id == c.id, ContestEntry.user_id == user.id))).all()
        data["mine"] = [{"entry_id": en.id, "publication_id": en.publication_id, "publication_status": st,
                         "disqualified": en.disqualified} for en, st in mine]
        data["eligible"] = await _eligible(session, c, user) if C.phase(c) == "en_cours" else []
    return data


async def _eligible(session: AsyncSession, c: Contest, user: User) -> list[dict]:
    """Les chapitres de l'auteur qu'il peut encore inscrire (publiés ou en relecture)."""
    rows = (await session.execute(
        select(Publication, Episode).join(Episode, Episode.id == Publication.episode_id)
        .where(Publication.user_id == user.id, Publication.status.in_(("pending", "published")))
        .options(selectinload(Episode.series))
    )).all()
    entered = set((await session.execute(select(ContestEntry.publication_id).where(ContestEntry.contest_id == c.id))).scalars())
    out = []
    for p, e in rows:
        if p.id in entered:
            continue
        why = _why_not(c, e)
        out.append({"publication_id": p.id, "title": f"{e.series.title or 'Manga'} — {e.title or f'Épisode {e.number}'}",
                    "status": p.status, "ok": why is None, "why": tr(why)})
    return out


def _why_not(c: Contest, e: Episode) -> str | None:
    if c.style and e.series.style != c.style:
        return f"Ce concours impose le style {STYLES.get(c.style, {}).get('label', c.style)}."
    if c.new_only and aware(e.created_at) < aware(c.starts_at):
        return "Ce concours n'accepte que les chapitres créés depuis son ouverture."
    return None


class EnterIn(BaseModel):
    publication_id: str


@router.post("/contests/{slug}/entries", status_code=201)
async def enter(slug: str, body: EnterIn, user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    c = await _visible(session, slug)
    if C.phase(c) != "en_cours":
        raise HTTPException(409, "Les inscriptions ne sont pas ouvertes." if C.phase(c) == "a_venir" else "Les inscriptions sont closes.")
    row = (await session.execute(
        select(Publication, Episode).join(Episode, Episode.id == Publication.episode_id)
        .where(Publication.id == body.publication_id, Publication.user_id == user.id)
        .options(selectinload(Episode.series)))).first()
    if not row:
        raise HTTPException(404, "Chapitre introuvable.")
    p, e = row
    if p.status not in ("pending", "published"):
        raise HTTPException(409, "Proposez d'abord ce chapitre à la galerie depuis la page de l'épisode.")
    why = _why_not(c, e)
    if why:
        raise HTTPException(409, why)
    n = (await session.execute(select(func.count()).select_from(ContestEntry).where(
        ContestEntry.contest_id == c.id, ContestEntry.user_id == user.id))).scalar_one()
    if n >= c.max_entries:
        raise HTTPException(409, f"Vous avez déjà inscrit {n} histoire{'s' if n > 1 else ''} : c'est le maximum pour ce concours.")
    if (await session.execute(select(ContestEntry.id).where(ContestEntry.contest_id == c.id, ContestEntry.publication_id == p.id))).first():
        raise HTTPException(409, "Cette histoire est déjà inscrite.")
    en = ContestEntry(contest_id=c.id, publication_id=p.id, user_id=user.id)
    session.add(en)
    await session.commit()
    return {"entry_id": en.id, "publication_status": p.status}


@router.delete("/contests/{slug}/entries/{entry_id}")
async def leave(slug: str, entry_id: str, user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    c = await _visible(session, slug)
    en = await session.get(ContestEntry, entry_id)
    if not en or en.contest_id != c.id or en.user_id != user.id:
        raise HTTPException(404, "Inscription introuvable.")
    if C.phase(c) != "en_cours":
        raise HTTPException(409, "Le concours est clos : l'inscription ne peut plus être retirée.")
    await session.delete(en)
    await session.commit()
    return {"ok": True}


# ---------- Administration ----------

class PrizeIn(BaseModel):
    rank: int = Field(ge=1, le=20)
    credits: int = Field(default=0, ge=0, le=5000)
    studio_days: int = Field(default=0, ge=0, le=365)


class ContestIn(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    slug: str = Field(default="", max_length=80)
    theme: str = Field(default="", max_length=300)
    description: str = Field(default="", max_length=4000)
    rules: str = Field(default="", max_length=20000)
    title_en: str = Field(default="", max_length=120)
    theme_en: str = Field(default="", max_length=300)
    description_en: str = Field(default="", max_length=4000)
    rules_en: str = Field(default="", max_length=20000)
    style: str = Field(default="", max_length=20)
    new_only: bool = True
    max_entries: int = Field(default=1, ge=1, le=10)
    prizes: list[PrizeIn] = Field(default_factory=list, max_length=20)
    starts_at: datetime
    ends_at: datetime
    visible: bool = False

    @model_validator(mode="after")
    def _check(self):
        if aware(self.ends_at) <= aware(self.starts_at):
            raise ValueError("La clôture doit venir après l'ouverture.")
        if self.style and self.style not in STYLES:
            raise ValueError("Style inconnu.")
        if len({p.rank for p in self.prizes}) != len(self.prizes):
            raise ValueError("Deux lots pour le même rang.")
        return self


def _apply(c: Contest, b: ContestIn) -> None:
    c.title, c.theme, c.description, c.rules = b.title.strip(), b.theme.strip(), b.description.strip(), b.rules.strip()
    c.title_en, c.theme_en, c.description_en, c.rules_en = b.title_en.strip(), b.theme_en.strip(), b.description_en.strip(), b.rules_en.strip()
    c.style, c.new_only, c.max_entries, c.visible = b.style, b.new_only, b.max_entries, b.visible
    c.prizes = [p.model_dump() for p in sorted(b.prizes, key=lambda p: p.rank) if p.credits or p.studio_days]
    c.starts_at, c.ends_at = aware(b.starts_at), aware(b.ends_at)


async def _free_slug(session: AsyncSession, wanted: str, own_id: str | None = None) -> str:
    base = C.slugify(wanted)
    slug, i = base, 2
    while (found := (await session.execute(select(Contest.id).where(Contest.slug == slug))).scalar_one_or_none()) and found != own_id:
        slug, i = f"{base}-{i}", i + 1
    return slug


@router.get("/admin/contests", dependencies=[Depends(admin_user)])
async def admin_list(session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(Contest).order_by(Contest.starts_at.desc()))).scalars().all()
    counts = await _counts(session, [c.id for c in rows])
    return {"items": [contest_out(c, counts.get(c.id, 0), admin=True) for c in rows]}


@router.post("/admin/contests", status_code=201)
async def admin_create(body: ContestIn, admin: User = Depends(admin_user), session: AsyncSession = Depends(get_session)):
    c = Contest(slug=await _free_slug(session, body.slug or body.title))
    _apply(c, body)
    session.add(c)
    await session.flush()
    log(session, admin, "contest", "contest", c.id, f"Concours « {c.title} » créé" + (" et visible" if c.visible else " (brouillon)"))
    await session.commit()
    return contest_out(c, admin=True)


async def _get(session: AsyncSession, contest_id: str) -> Contest:
    c = await session.get(Contest, contest_id)
    if not c:
        raise HTTPException(404, "Concours introuvable.")
    return c


@router.put("/admin/contests/{contest_id}")
async def admin_update(contest_id: str, body: ContestIn, admin: User = Depends(admin_user), session: AsyncSession = Depends(get_session)):
    c = await _get(session, contest_id)
    if c.results_at:
        raise HTTPException(409, "Les résultats sont proclamés : le concours ne se modifie plus.")
    if body.slug and C.slugify(body.slug) != c.slug:
        c.slug = await _free_slug(session, body.slug, c.id)
    _apply(c, body)
    log(session, admin, "contest", "contest", c.id, f"Concours « {c.title} » modifié" + ("" if c.visible else " (brouillon)"))
    await session.commit()
    return contest_out(c, admin=True)


@router.get("/admin/contests/{contest_id}", dependencies=[Depends(admin_user)])
async def admin_get(contest_id: str, session: AsyncSession = Depends(get_session)):
    c = await _get(session, contest_id)
    entries = await _entries_view(session, c, None, admin=True)
    data = contest_out(c, sum(1 for e in entries if not e["disqualified"] and e["publication_status"] == "published"), admin=True)
    data["entries_list"] = entries
    return data


class JuryIn(BaseModel):
    jury_score: float | None = Field(default=None, ge=0, le=20)
    disqualified: str | None = Field(default=None, max_length=300)


@router.post("/admin/contests/{contest_id}/entries/{entry_id}")
async def admin_entry(contest_id: str, entry_id: str, body: JuryIn, admin: User = Depends(admin_user), session: AsyncSession = Depends(get_session)):
    c = await _get(session, contest_id)
    en = await session.get(ContestEntry, entry_id)
    if not en or en.contest_id != c.id:
        raise HTTPException(404, "Inscription introuvable.")
    if c.results_at:
        raise HTTPException(409, "Les résultats sont proclamés.")
    if body.jury_score is not None:
        en.jury_score = round(body.jury_score, 2)
    if body.disqualified is not None:
        en.disqualified = body.disqualified.strip()
        log(session, admin, "contest", "user", en.user_id,
            f"Concours « {c.title} » : " + (f"histoire disqualifiée — {en.disqualified}" if en.disqualified else "histoire remise en lice"))
    await session.commit()
    return {"jury_score": en.jury_score, "disqualified": en.disqualified}


@router.post("/admin/contests/{contest_id}/results")
async def admin_results(contest_id: str, admin: User = Depends(admin_user), session: AsyncSession = Depends(get_session)):
    """Proclame les résultats : classement figé, lots crédités. Irréversible."""
    c = await _get(session, contest_id)
    if C.phase(c) != "deliberation":
        raise HTTPException(409, "Les résultats se proclament après la clôture, une seule fois.")
    entries = await C.eligible_entries(session, c)
    missing = sum(1 for e in entries if e.jury_score is None)
    if missing:
        raise HTTPException(409, f"Il manque la note du jury pour {missing} histoire{'s' if missing > 1 else ''}.")
    ranked = await C.proclaim(session, c)
    winners = [f"{C.rank_label(e.rank)} : {e.prize}" for e in ranked if e.prize]
    log(session, admin, "contest_results", "contest", c.id,
        f"Résultats du concours « {c.title} » ({len(ranked)} histoires)" + (" — " + " ; ".join(winners) if winners else ""))
    await session.commit()
    return {"ranked": len(ranked), "results_at": iso(c.results_at)}


async def awards_for(session: AsyncSession, publication_id: str) -> list[dict]:
    """Prix gagnés par une histoire (affichés sur sa page de lecture)."""
    rows = (await session.execute(
        select(ContestEntry.rank, ContestEntry.prize, Contest.title, Contest.title_en, Contest.slug).join(Contest, Contest.id == ContestEntry.contest_id)
        .where(ContestEntry.publication_id == publication_id, ContestEntry.prize != "", Contest.results_at.is_not(None))
    )).all()
    en = lang() == "en"
    return [{"rank": r, "label": f"{C.rank_label(r, 'en' if en else 'fr')} — {(te if en and te else t)}", "slug": s} for r, _, t, te, s in rows]

