"""Fabrication du PDF d'un chapitre (Pillow). Comptes gratuits : filigrane MangaStudio sur chaque page."""
import io
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

PAGE_W, PAGE_H = 1024, 1536
INK = (20, 17, 15)
PAPER = (255, 253, 248)
RED = (217, 54, 30)


# Police avec accents (paquet fonts-dejavu-core de l'image Docker ; souvent présente sous Linux).
POLICES = [Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"), Path("C:/Windows/Fonts/arialbd.ttf")]


def _police() -> Path | None:
    return next((p for p in POLICES if p.exists()), None)


def _font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    if (p := _police()):
        return ImageFont.truetype(str(p), size)
    try:
        return ImageFont.load_default(size=size)    # police intégrée à Pillow : sans accents
    except TypeError:
        return ImageFont.load_default()


def _texte(t: str) -> str:
    """Sans vraie police, les lettres accentuées s'affichent en carrés : on les retire."""
    if _police():
        return t
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()


def _page(data: bytes | None, number: int) -> Image.Image:
    try:
        if data is None:
            raise UnidentifiedImageError
        img = Image.open(io.BytesIO(data))
        img.load()
        return img.convert("RGB")
    except (UnidentifiedImageError, OSError):
        # Image illisible (format vectoriel de démonstration, fichier manquant) : page de remplacement.
        img = Image.new("RGB", (PAGE_W, PAGE_H), PAPER)
        d = ImageDraw.Draw(img)
        d.rectangle((24, 24, PAGE_W - 24, PAGE_H - 24), outline=INK, width=6)
        d.text((PAGE_W // 2, PAGE_H // 2), f"Page {number}", font=_font(72), fill=INK, anchor="mm")
        return img


def _filigrane(img: Image.Image, mention: str) -> Image.Image:
    w, h = img.size
    calque = Image.new("RGBA", img.size, (0, 0, 0, 0))
    # Grand « MangaStudio » en diagonale, discret mais impossible à rogner sans abîmer la page.
    texte = Image.new("RGBA", (int(w * 1.4), int(h * 0.2)), (0, 0, 0, 0))
    ImageDraw.Draw(texte).text((texte.width // 2, texte.height // 2), "MangaStudio", font=_font(int(w * 0.16)),
                               fill=(*INK, 46), anchor="mm")
    texte = texte.rotate(56, expand=True)
    calque.alpha_composite(texte, ((w - texte.width) // 2, (h - texte.height) // 2))
    # Bandeau en bas de page avec l'adresse du site.
    bande = int(h * 0.045)
    d = ImageDraw.Draw(calque)
    d.rectangle((0, h - bande, w, h), fill=(*PAPER, 235))
    d.line((0, h - bande, w, h - bande), fill=(*INK, 255), width=3)
    d.text((w // 2, h - bande // 2), _texte(mention), font=_font(int(bande * 0.42)), fill=(*INK, 255), anchor="mm")
    return Image.alpha_composite(img.convert("RGBA"), calque).convert("RGB")


def build(images: list[bytes | None], *, watermark: bool, title: str, mention: str) -> bytes:
    pages = [_page(data, i + 1) for i, data in enumerate(images)] or [_page(None, 1)]
    if watermark:
        pages = [_filigrane(p, mention) for p in pages]
    out = io.BytesIO()
    pages[0].save(out, "PDF", save_all=True, append_images=pages[1:], resolution=150, quality=85,
                  title=title, author="MangaStudio", creator="MangaStudio")
    return out.getvalue()
