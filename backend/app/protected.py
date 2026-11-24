"""Personnages célèbres protégés par le droit d'auteur.

Le dessinateur IA refuse de les dessiner : un épisode qui en contient s'arrête au dessin.
On les repère dès la saisie pour que l'auteur invente son propre personnage avant de dépenser quoi que ce soit.

Liste volontairement courte : seulement des noms sans ambiguïté (pas de « Mario », « Elsa » ou « Thor »,
qui sont aussi des prénoms). Pour en ajouter, écrivez-les en minuscules, sans accents.
"""
import re

from app.moderation import normalize

NOMS = [
    # Mangas et animés
    "sonic", "naruto", "sasuke", "kakashi", "goku", "son goku", "sangoku", "vegeta", "dragon ball", "pikachu", "pokemon",
    "luffy", "monkey d luffy", "one piece", "ichigo kurosaki", "tanjiro", "nezuko", "demon slayer", "satoru gojo",
    "eren yeager", "eren jaeger", "mikasa ackerman", "levi ackerman", "saitama", "light yagami", "doraemon", "totoro",
    "sailor moon", "ash ketchum", "boruto", "deku", "izuku midoriya", "all might", "jojo", "hunter x hunter",
    # Bandes dessinées, films, jeux
    "spider man", "spiderman", "batman", "superman", "wonder woman", "iron man", "captain america", "black panther",
    "deadpool", "wolverine", "hulk", "mickey", "minnie mouse", "donald duck", "simba", "shrek", "darth vader", "yoda",
    "harry potter", "hermione granger", "super mario", "zelda", "kirby", "lara croft", "kratos", "tintin", "asterix",
    "obelix", "lucky luke", "spongebob", "bob l eponge", "kirikou",
]
_RE = re.compile(r"\b(" + "|".join(re.escape(normalize(n)) for n in sorted(NOMS, key=len, reverse=True)) + r")\b")


def find(text: str) -> str | None:
    """Le premier nom protégé trouvé dans le texte (comparaison sans accents ni majuscules), ou None."""
    m = _RE.search(normalize(text or ""))
    return m.group(1) if m else None


def message(nom: str) -> str:
    return (f"« {nom.title()} » est un personnage protégé par le droit d'auteur : le dessinateur IA refusera de le dessiner. "
            "Inventez votre propre personnage (un autre nom et une autre apparence) : vous pourrez lui donner le même caractère.")
