"""Modèles Muse de Meta, par la Meta Model API (https://api.meta.ai/v1).

  - MuseText  : muse-wonder (scénario) et muse-spark (vision : design, relecture, modération),
                sortie JSON stricte par /chat/completions.
  - MuseImage : muse-image, /images/generations sans référence, /images/edits avec
                1 à 10 images de référence.

Le format des appels suit celui qu'utilise le projet Acid contre cette API (corps
JSON, références en `images: [{image_url}]`, image rendue en `b64_json`). Il n'a pas
été testé ici avec une vraie clé : lancer scripts/banc_essai.py pour le valider.
"""
import asyncio
import base64
import json
import re

import httpx

from app.providers.base import ContentBlocked, ImageResult, ProviderError, TextResult, Usage

MAX_REFERENCES = 10
RETRIES = 5


def _sniff(data: bytes) -> str:
    """Type MIME d'après les premiers octets (l'API ne le dit pas toujours)."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"


def _data_url(data: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


class _Muse:
    name = "meta_muse"

    def __init__(self, base_url: str, api_key: str, transport: httpx.AsyncBaseTransport | None = None):
        self.base_url = (base_url or "https://api.meta.ai/v1").rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.transport = transport   # injecté par les tests

    async def post(self, path: str, body: dict) -> dict:
        """POST JSON avec reprise sur 429 (attente longue) et 5xx (attente courte)."""
        async with httpx.AsyncClient(timeout=300, transport=self.transport) as client:
            for attempt in range(RETRIES):
                try:
                    res = await client.post(f"{self.base_url}{path}", headers=self.headers, json=body)
                except httpx.RequestError as e:
                    if attempt == RETRIES - 1:
                        raise ProviderError(f"Meta injoignable : {e}") from e
                    await asyncio.sleep(2**attempt)
                    continue
                if res.is_success:
                    return res.json()
                text = res.text[:600]
                try:
                    err = res.json().get("error") or {}
                except ValueError:
                    err = {}
                kind = err.get("type") or ""
                message = err.get("message") or text
                if "content_policy" in kind or re.search(r"content.?policy|safety", text, re.I):
                    raise ContentBlocked(message)
                retryable = res.status_code == 429 or res.status_code >= 500
                if not retryable or attempt == RETRIES - 1:
                    error = ProviderError(f"Meta {res.status_code} : {message}")
                    error.status, error.param = res.status_code, str(err.get("param") or "")   # type: ignore[attr-defined]
                    raise error
                wait = float(res.headers.get("retry-after") or 0)
                await asyncio.sleep(max(wait, min(2 * 2**attempt, 15) if res.status_code == 429 else 0.7 * 2**attempt))
        raise ProviderError("Meta : aucune réponse")


class MuseText(_Muse):
    async def json(self, *, model, system, user, schema, schema_name, images=None, max_tokens=16000) -> TextResult:
        content: list[dict] | str = user
        if images:
            content = [{"type": "text", "text": user}] + [
                {"type": "image_url", "image_url": {"url": _data_url(data, mime)}} for data, mime in images]
        body = await self.post("/chat/completions", {
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}],
            "response_format": {"type": "json_schema", "json_schema": {"name": schema_name, "schema": schema, "strict": True}},
            "reasoning_effort": "low",
            # Le budget couvre aussi les tokens de raisonnement : large, pour ne jamais tronquer le JSON.
            "max_completion_tokens": max(max_tokens, 8000),
        })
        choice = (body.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        text = message.get("content")
        if not text:
            if message.get("refusal"):
                raise ContentBlocked(message["refusal"])
            raise ProviderError(f"Meta : réponse vide ({choice.get('finish_reason', 'sans motif')})")
        try:
            data = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip()))
        except json.JSONDecodeError as e:
            raise ProviderError(f"Meta : JSON illisible ({e})") from e
        u = body.get("usage") or {}
        return TextResult(data, Usage(u.get("prompt_tokens", 0), u.get("completion_tokens", 0)))


class MuseImage(_Muse):
    async def draw(self, *, model, prompt, references, size="1024x1536") -> ImageResult:
        if not references:
            body = await self.post("/images/generations", {
                "model": model, "prompt": prompt, "n": 1, "size": size, "response_format": "b64_json"})
        else:
            payload = {"model": model, "prompt": prompt, "n": 1, "size": size,
                       "images": [{"image_url": _data_url(data, mime)} for data, mime in references[:MAX_REFERENCES]]}
            try:
                body = await self.post("/images/edits", payload)
            except ProviderError as e:
                # La doc ne dit pas si l'édition accepte `size` : on le retire une fois si l'API le refuse.
                if getattr(e, "status", 0) != 400 or "size" not in f"{getattr(e, 'param', '')} {e}".lower():
                    raise
                payload.pop("size")
                body = await self.post("/images/edits", payload)
        item = (body.get("data") or [{}])[0]
        if not item.get("b64_json"):
            raise ProviderError("Meta : aucune image renvoyée")
        image = base64.b64decode(item["b64_json"])
        return ImageResult(image, _sniff(image))
