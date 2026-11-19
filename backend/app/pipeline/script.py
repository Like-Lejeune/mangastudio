"""Le scénario d'un épisode : schéma JSON demandé au scénariste, et normalisation.

Le schéma est construit pour chaque épisode (nombre de pages exact, identifiants
des personnages en énumération). La normalisation ré-impose tout côté serveur :
le dessinateur ne reçoit jamais un scénario mal formé."""

MAX_PANELS = 6
MAX_LINES = 2
MAX_WORDS = 14
NARRATOR = "narrator"


class ScriptIncomplete(Exception):
    pass


def _panel_schema(cast: list[str]) -> dict:
    line = {
        "type": "object", "additionalProperties": False, "required": ["speaker", "text", "kind"],
        "properties": {
            "speaker": {"type": "string", "enum": [*cast, NARRATOR]},
            "text": {"type": "string", "description": f"at most {MAX_WORDS} words"},
            "kind": {"type": "string", "enum": ["speech", "thought", "shout", "caption"]},
        },
    }
    return {
        "type": "object", "additionalProperties": False,
        "required": ["size", "shot", "action", "characters", "lines", "sfx"],
        "properties": {
            "size": {"type": "string", "enum": ["wide", "tall", "square", "small"]},
            "shot": {"type": "string", "description": "camera framing and angle"},
            "action": {"type": "string", "description": "what is visible: poses, expressions, props, place"},
            "characters": {"type": "array", "items": {"type": "string", "enum": cast}, "description": "ids of the characters visible"},
            "lines": {"type": "array", "items": line, "maxItems": MAX_LINES},
            "sfx": {"type": "string", "description": "one short sound effect, or empty"},
        },
    }


def pages_schema(count: int, cast: list[str]) -> dict:
    # Certains fournisseurs refusent minItems/maxItems en mode strict : les retirer
    # dans l'adaptateur si besoin, normalise() impose les comptes de toute façon.
    return {
        "type": "array", "minItems": count, "maxItems": count,
        "items": {
            "type": "object", "additionalProperties": False, "required": ["number", "beat", "panels"],
            "properties": {
                "number": {"type": "integer"},
                "beat": {"type": "string", "description": "what this page does for the story, one sentence"},
                "panels": {"type": "array", "minItems": 3, "maxItems": MAX_PANELS, "items": _panel_schema(cast)},
            },
        },
    }


_META = {
    "title": {"type": "string", "description": "series title"},
    "episode_title": {"type": "string", "description": "this episode's title, at most 6 words"},
    "tagline": {"type": "string", "description": "one cover line, at most 10 words"},
    "setting": {"type": "string", "description": "place and time, visually specific"},
    "summary": {"type": "string", "description": "2-3 sentences: what happens and where it leaves everyone"},
}


def script_schema(page_count: int, cast: list[str]) -> dict:
    """Scénario complet en un appel."""
    return {"type": "object", "additionalProperties": False, "required": [*_META, "pages"],
            "properties": {**_META, "pages": pages_schema(page_count, cast)}}


def outline_schema(page_count: int) -> dict:
    """Première passe des épisodes longs : le plan, une phrase par page."""
    return {"type": "object", "additionalProperties": False, "required": [*_META, "beats"],
            "properties": {**_META, "beats": {"type": "array", "minItems": page_count, "maxItems": page_count, "items": {"type": "string"}}}}


def batch_schema(count: int, cast: list[str]) -> dict:
    """Deuxième passe : un lot de pages."""
    return {"type": "object", "additionalProperties": False, "required": ["pages"],
            "properties": {"pages": pages_schema(count, cast)}}


def normalise_pages(pages: list[dict], count: int, cast: list[str], max_per_page: int, first_number: int = 1) -> list[dict]:
    """Impose le nombre de pages et de cases, ne garde que les personnages connus,
    et limite le nombre de personnages par page à ce que le dessinateur sait suivre."""
    if len(pages) < count:
        raise ScriptIncomplete(f"{len(pages)} pages reçues, {count} attendues")
    known = set(cast)
    out = []
    for offset, page in enumerate(pages[:count]):
        panels = (page.get("panels") or [])[:MAX_PANELS]
        if not panels:
            raise ScriptIncomplete(f"page {first_number + offset} sans case")
        kept: list[str] = []                       # personnages de la page, dans l'ordre d'apparition
        for panel in panels:
            for slug in panel.get("characters") or []:
                if slug in known and slug not in kept:
                    kept.append(slug)
        allowed = set(kept[:max_per_page])
        clean = []
        for panel in panels:
            lines = []
            for line in (panel.get("lines") or [])[:MAX_LINES]:
                words = str(line.get("text", "")).split()
                if not words:
                    continue
                speaker = line.get("speaker")
                lines.append({
                    "speaker": speaker if speaker in allowed else NARRATOR,
                    "text": " ".join(words[:MAX_WORDS]),
                    "kind": line.get("kind") if line.get("kind") in ("speech", "thought", "shout", "caption") else "speech",
                })
            sfx = str(panel.get("sfx") or "").strip()
            clean.append({
                "size": panel.get("size") if panel.get("size") in ("wide", "tall", "square", "small") else "square",
                "shot": str(panel.get("shot", "")),
                "action": str(panel.get("action", "")),
                "characters": list(dict.fromkeys(s for s in panel.get("characters") or [] if s in allowed)),
                "lines": lines,
                "sfx": sfx if len(sfx) <= 12 else "",
            })
        out.append({"number": first_number + offset, "beat": str(page.get("beat", "")), "panels": clean})
    return out


def script_text(script: dict) -> str:
    """Tout le texte du scénario, pour le contrôle des mots bloqués."""
    parts = [script.get("title", ""), script.get("episode_title", ""), script.get("tagline", "")]
    for page in script["pages"]:
        for panel in page["panels"]:
            parts.append(panel["action"])
            parts.extend(line["text"] for line in panel["lines"])
    return "\n".join(parts)
