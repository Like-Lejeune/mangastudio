"""Dessine une page d'exemple pour chaque style, avec le vrai modèle d'image du .env (Muse).

    cd backend
    python -m scripts.exemples_styles              tous les styles (5 images, quelques centimes)
    python -m scripts.exemples_styles afro shojo   seulement ceux-là, pour refaire une image ratée

Les images vont dans frontend/public/styles/<style>.webp : la page « Styles » et le choix du
style à la création d'une série les affichent. Regardez-les avant de les publier (git add),
et relancez un style si l'image ne vous plaît pas : chaque tirage est différent.
"""
import asyncio
import io
import sys
from pathlib import Path

from app.config import get_settings
from app.pipeline.prompts import STYLES, art, ink
from app.providers import get_studio

DOSSIER = Path(__file__).resolve().parents[2] / "frontend" / "public" / "styles"

# Une scène par style, choisie pour montrer ce qui le caractérise.
SCENES = {
    "shonen": "Three panels. 1: a young courier on a scooter jumps over a fruit stall, chased by a masked rival, speed lines. "
              "2: close-up of her fierce determined eyes. 3: wide shot of both landing on a rooftop at sunset, the city below.",
    "shojo": "Three panels. 1: two classmates share an umbrella under blossoming jacaranda trees after school, petals drifting. "
             "2: close-up of a shy smile and sparkling eyes, decorative flowers around. 3: their hands almost touching on the umbrella handle.",
    "seinen": "Three panels. 1: a weary detective in a long coat inspects a shipping container in a rain-soaked port at night. "
              "2: close-up of his hands holding a torn photograph. 3: his silhouette under a lone streetlight, heavy shadows.",
    "kodomo": "Three panels. 1: a little boy and his talking goat set off with a picnic basket on a sunny path. "
              "2: the goat sneezes comically, the boy laughs. 3: both wave at a smiling sun above round green hills.",
    "afro": "Three panels. 1: a young woman in a bold wax-print outfit runs through a busy Yaoundé market at dusk, moto-taxis passing. "
            "2: close-up of her braided hair, headwrap and determined eyes. 3: wide shot of her on a hilltop above the city lights, "
            "kente-patterned scarf in the wind.",
}


def prompt(style: str) -> str:
    return (f"A single manga page in {art(style)}. {SCENES[style]} "
            "Clear panel borders, no speech bubbles, no text, no lettering, no sound effects. " + ink("bw"))


def en_webp(data: bytes) -> bytes:
    """Réduit l'image pour le site (environ 100 Ko) ; garde l'original si Pillow manque."""
    try:
        from PIL import Image
    except ImportError:
        return data
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img.thumbnail((720, 1080))
    out = io.BytesIO()
    img.save(out, "WEBP", quality=82)
    return out.getvalue()


async def main(styles: list[str]) -> int:
    s = get_settings()
    if s.image_provider == "fake":
        print("IMAGE_PROVIDER=fake : configurez Muse dans backend/.env avant de lancer ce script.")
        return 1
    inconnus = [x for x in styles if x not in SCENES]
    if inconnus:
        print(f"Styles inconnus : {', '.join(inconnus)}. Disponibles : {', '.join(SCENES)}")
        return 1
    studio = get_studio()
    DOSSIER.mkdir(parents=True, exist_ok=True)
    print(f"Modèle : {studio.artist_model} · {len(styles)} image(s) → {DOSSIER}\n")

    async def un(style: str) -> tuple[str, str]:
        try:
            r = await studio.artist.draw(model=studio.artist_model, prompt=prompt(style), references=[], size="1024x1536")
        except Exception as e:  # noqa: BLE001  (un style raté ne doit pas empêcher les autres)
            return style, f"échec : {e}"
        chemin = DOSSIER / f"{style}.webp"
        chemin.write_bytes(en_webp(r.image))
        return style, f"{chemin.name} ({chemin.stat().st_size // 1024} Ko)"

    ok = True
    for style, resultat in await asyncio.gather(*(un(x) for x in styles)):
        ok &= not resultat.startswith("échec")
        print(f"  {STYLES[style]['label']:<11} {resultat}")
    print("\nOuvrez les images, relancez celles qui ne vous plaisent pas, puis : git add frontend/public/styles")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:] or list(SCENES))))
