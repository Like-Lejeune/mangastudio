"""Partage d'un chapitre par lien public, page de lecture sans compte, et téléchargement PDF."""
import asyncio
import html
import secrets
from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import growth, i18n, pdf, storage
from app.config import get_settings
from app.db import get_session
from app.models import Episode, PdfDownload, User
from app.routers.episodes import owned_episode
from app.security import verified_user
from app.services import current_plan

router = APIRouter(tags=["partage"])
FREE_PDF_PER_MONTH = 3


def app_url() -> str:
    return get_settings().frontend_url.split(",")[0].strip().rstrip("/")


def share_url(token: str) -> str:
    return f"{app_url()}/lire/{token}"


# ---------- Partage ----------

class ShareIn(BaseModel):
    enabled: bool


@router.post("/episodes/{episode_id}/share")
async def set_share(episode_id: str, body: ShareIn, user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    """Active (nouveau lien) ou coupe le lien public. Un lien coupé ne fonctionne plus jamais."""
    e = await owned_episode(session, user, episode_id)
    if body.enabled:
        if e.status != "done":
            raise HTTPException(409, "Seul un épisode terminé peut être partagé.")
        if not e.share_token:
            e.share_token = secrets.token_urlsafe(16)[:22]
            await growth.mission(session, user.id, "first_share")
    else:
        e.share_token = None
    await session.commit()
    return {"enabled": bool(e.share_token), "url": share_url(e.share_token) if e.share_token else None}


async def _shared(session: AsyncSession, token: str) -> Episode | None:
    if not token or len(token) > 32:
        return None
    return (await session.execute(
        select(Episode).where(Episode.share_token == token, Episode.status == "done")
        .options(selectinload(Episode.pages), selectinload(Episode.series))
    )).scalar_one_or_none()


_LIRE = {
    "fr": {"gone_h": "Ce chapitre n'est plus partagé", "gone_p": "Son auteur a coupé le lien, ou il n'existe pas.",
           "own": "Créer mon propre manga", "gone_t": "Chapitre introuvable — MangaStudio", "ep": "Épisode", "by": "par",
           "someone": "un auteur", "pages": "pages", "og": "Un manga de {a}, créé avec MangaStudio.", "page": "Page",
           "you_too": "Vous aussi, racontez votre histoire.", "how": "Décrivez une idée, MangaStudio dessine les pages.",
           "cta": "Créer mon manga gratuitement"},
    "en": {"gone_h": "This chapter is no longer shared", "gone_p": "Its author turned off the link, or it doesn't exist.",
           "own": "Create my own manga", "gone_t": "Chapter not found — MangaStudio", "ep": "Episode", "by": "by",
           "someone": "an author", "pages": "pages", "og": "A manga by {a}, made with MangaStudio.", "page": "Page",
           "you_too": "Tell your own story too.", "how": "Describe an idea, MangaStudio draws the pages.",
           "cta": "Create my manga for free"},
}


def _page_html(title: str, body: str, meta: str = "", lang: str = "fr") -> str:
    return f"""<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>{title}</title>{meta}
<style>
body{{margin:0;background:#F7F3EA;color:#14110F;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.5}}
header,footer{{max-width:820px;margin:0 auto;padding:20px 16px}}
.marque{{font-weight:800;font-size:22px;color:#14110F;text-decoration:none}}.marque span{{color:#D9361E}}
h1{{font-size:28px;line-height:1.2;margin:16px 0 4px}}.sous{{color:#5b544b;margin:0}}
main{{max-width:820px;margin:0 auto;padding:0 16px;display:flex;flex-direction:column;gap:16px}}
main img{{width:100%;height:auto;display:block;border:2px solid #14110F;background:#fff}}
.cta{{display:inline-block;margin-top:12px;background:#D9361E;color:#fff;font-weight:700;padding:14px 22px;border:2px solid #14110F;border-radius:4px;box-shadow:4px 4px 0 #14110F;text-decoration:none}}
footer{{text-align:center;padding-bottom:48px}}
</style></head><body>{body}</body></html>"""


@router.get("/lire/{token}", response_class=HTMLResponse, include_in_schema=False)
async def read_shared(token: str, session: AsyncSession = Depends(get_session)):
    """Page de lecture publique. Rendue par le serveur pour que WhatsApp et Facebook affichent l'aperçu.
    Elle est dans la langue de l'histoire (celle des dialogues) ; un lien introuvable suit la langue du visiteur."""
    e = await _shared(session, token)
    inscription = f"{app_url()}/inscription"
    if not e:
        t = _LIRE["en" if i18n.lang() == "en" else "fr"]
        body = (f'<header><a class="marque" href="{app_url()}">Manga<span>Studio</span></a></header>'
                f'<main><h1>{t["gone_h"]}</h1><p class="sous">{t["gone_p"]}</p>'
                f'<p><a class="cta" href="{inscription}">{t["own"]}</a></p></main>')
        return HTMLResponse(_page_html(t["gone_t"], body, lang=i18n.lang()), status_code=404)
    lang = "en" if e.series.language == "en" else "fr"
    t = _LIRE[lang]
    owner = await session.get(User, e.series.owner_id)
    if owner:      # le bouton d'inscription porte le code de parrainage de l'auteur
        inscription = f"{inscription}?ref={await growth.ensure_code(session, owner)}"
        await session.commit()
    serie = html.escape(e.series.title or "Manga")
    titre = f"{serie} — {t['ep']} {e.number}" + (f" : {html.escape(e.title)}" if e.title else "")
    auteur = html.escape(owner.display_name) if owner else t["someone"]
    pages = [p for p in e.pages if p.image_path]
    image = storage.url(e.series.cover_path) or (storage.url(pages[0].image_path) if pages else None)
    resume = html.escape((e.summary or e.series.premise or "")[:200])
    lien = share_url(token)
    meta = (f'<meta name="description" content="{resume}">'
            f'<meta property="og:type" content="article"><meta property="og:site_name" content="MangaStudio">'
            f'<meta property="og:title" content="{titre}"><meta property="og:description" content="{t["og"].format(a=auteur)} {resume}">'
            f'<meta property="og:locale" content="{"en_GB" if lang == "en" else "fr_FR"}">'
            f'<meta property="og:url" content="{lien}">'
            + (f'<meta property="og:image" content="{image}"><meta name="twitter:card" content="summary_large_image">' if image else ""))
    images = "".join(
        f'<img src="{storage.url(p.image_path)}" alt="{t["page"]} {p.number}" loading="{"eager" if i < 2 else "lazy"}">'
        for i, p in enumerate(pages))
    body = (f'<header><a class="marque" href="{app_url()}">Manga<span>Studio</span></a>'
            f'<h1>{titre}</h1><p class="sous">{t["by"]} {auteur} · {len(pages)} {t["pages"]}</p></header>'
            f'<main>{images}</main>'
            f'<footer><p><b>{t["you_too"]}</b><br>{t["how"]}</p>'
            f'<a class="cta" href="{inscription}">{t["cta"]}</a></footer>')
    return HTMLResponse(_page_html(f"{titre} — MangaStudio", body, meta, lang))


# ---------- PDF ----------

def _month_start() -> datetime:
    n = datetime.now(timezone.utc)
    return n.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


async def pdf_quota(session: AsyncSession, user: User) -> dict:
    """Payant : illimité, sans filigrane. Gratuit : 3 chapitres différents par mois, avec filigrane."""
    plan, _ = await current_plan(session, user.id)
    if plan.id != "free":
        return {"limit": None, "used": 0, "watermark": False}
    used = (await session.execute(
        select(func.count(func.distinct(PdfDownload.episode_id)))
        .where(PdfDownload.user_id == user.id, PdfDownload.created_at >= _month_start())
    )).scalar_one()
    return {"limit": FREE_PDF_PER_MONTH, "used": used, "watermark": True}


@router.get("/me/pdf-quota")
async def my_pdf_quota(user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    return await pdf_quota(session, user)


@router.get("/episodes/{episode_id}/pdf")
async def download_pdf(episode_id: str, user: User = Depends(verified_user), session: AsyncSession = Depends(get_session)):
    e = await owned_episode(session, user, episode_id)
    if e.status != "done":
        raise HTTPException(409, "Le chapitre n'est pas terminé.")
    quota = await pdf_quota(session, user)
    if quota["limit"] is not None:
        deja = (await session.execute(select(PdfDownload.id).where(
            PdfDownload.user_id == user.id, PdfDownload.episode_id == e.id, PdfDownload.created_at >= _month_start()))).first()
        if not deja and quota["used"] >= quota["limit"]:
            raise HTTPException(402, {"code": "pdf_quota", "message": f"Vous avez téléchargé {quota['limit']} chapitres ce mois-ci. "
                                      "Passez à un plan payant pour des PDF illimités et sans filigrane."})
    images = []
    for p in e.pages:
        try:
            images.append(await storage.load(p.image_path) if p.image_path else None)
        except OSError:
            images.append(None)
    en = (user.locale or i18n.lang()) == "en"
    titre = f"{e.series.title or 'Manga'} — {'Episode' if en else 'Épisode'} {e.number}"
    code = await growth.ensure_code(session, user)
    site = app_url().split("://")[-1]
    data = await asyncio.to_thread(pdf.build, images, watermark=quota["watermark"], title=titre,
                                   mention=f"Made with MangaStudio · {site} · code {code}" if en else f"Créé avec MangaStudio · {site} · code {code}")
    session.add(PdfDownload(user_id=user.id, episode_id=e.id, watermark=quota["watermark"]))
    await session.commit()
    nom = f"{e.series.title or 'manga'} - episode {e.number}.pdf"
    return Response(data, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=\"episode-{e.number}.pdf\"; filename*=UTF-8''{quote(nom)}"})
