"""Fournisseurs factices : aucun appel réseau, aucune dépense.
Le texte est fabriqué à partir du schéma JSON demandé ; l'image est un SVG étiqueté."""
from html import escape

from app.providers.base import ImageResult, TextResult, Usage


def _fill(schema: dict, key: str = "", index: int = 0):
    """Construit une valeur valide pour `schema`."""
    if "enum" in schema:
        return schema["enum"][index % len(schema["enum"])]
    kind = schema.get("type")
    if kind == "object":
        return {k: _fill(v, k, index) for k, v in schema.get("properties", {}).items()}
    if kind == "array":
        n = schema.get("minItems", 0 if key == "violations" else 1)
        return [_fill(schema["items"], key, i) for i in range(n)]
    if kind == "boolean":
        return key in ("pass", "passed", "allowed")
    if kind == "integer":
        return index + 1
    if kind == "string":
        if key in ("fix", "sfx", "rule"):
            return ""
        return f"{key or 'texte'} {index + 1}"
    return None


class FakeText:
    name = "fake"

    async def json(self, *, model, system, user, schema, schema_name, images=None, max_tokens=16000) -> TextResult:
        data = _fill(schema)
        usage = Usage(input_tokens=(len(system) + len(user)) // 4 + 1500 * len(images or []), output_tokens=len(str(data)) // 4)
        return TextResult(data, usage)


class FakeImage:
    name = "fake"

    async def draw(self, *, model, prompt, references, size="1024x1536") -> ImageResult:
        w, h = size.split("x")
        label = escape(prompt.splitlines()[0][:42])
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">'
            f'<rect width="100%" height="100%" fill="#f4f1ea" stroke="#111" stroke-width="12"/>'
            f'<text x="50%" y="48%" text-anchor="middle" font-family="sans-serif" font-size="34">{label}</text>'
            f'<text x="50%" y="54%" text-anchor="middle" font-family="sans-serif" font-size="26" fill="#666">'
            f"{len(references)} image(s) de référence</text></svg>"
        )
        return ImageResult(svg.encode(), "image/svg+xml")
