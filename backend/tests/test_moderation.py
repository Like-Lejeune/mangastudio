from app.moderation import find_terms, normalize
from app.pipeline.script import normalise_pages


def test_normalize():
    assert normalize("Sèxe !!") == "sexe"
    assert normalize("S3X3") == "sexe"
    assert normalize("seeeexe") == "sexe"


def test_terms_match_whole_words_only():
    terms = ["sexe", "arme a feu"]
    assert find_terms("Une scène de SÈXE.", terms) == ["sexe"]
    assert find_terms("s e x e", terms) == ["sexe"]
    assert find_terms("s3xe", terms) == ["sexe"]
    assert find_terms("Il sort une arme à feu !", terms) == ["arme a feu"]
    assert find_terms("Le Sussex et ses sexagénaires", terms) == []


def _panel(chars):
    return {"size": "wide", "shot": "plan large", "action": "ils courent", "characters": chars,
            "lines": [{"speaker": chars[0], "text": "mot " * 30, "kind": "speech"}], "sfx": ""}


def test_normalise_limits_characters_per_page():
    cast = ["a", "b", "c", "d"]
    pages = [{"number": 9, "beat": "x", "panels": [_panel(["a", "b"]), _panel(["c", "zz"]), _panel(["d", "a"])]}]
    out = normalise_pages(pages, 1, cast, max_per_page=3)
    assert out[0]["number"] == 1
    assert [p["characters"] for p in out[0]["panels"]] == [["a", "b"], ["c"], ["a"]]
    assert out[0]["panels"][2]["lines"][0]["speaker"] == "narrator"      # "d" n'est plus sur la page
    assert len(out[0]["panels"][0]["lines"][0]["text"].split()) == 14
