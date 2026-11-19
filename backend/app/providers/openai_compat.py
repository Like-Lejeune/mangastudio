"""Adaptateur pour les API au format OpenAI (chat/completions, images).
Couvre la plupart des fournisseurs et des relais ; pour un fournisseur au format
différent, écrire une classe sœur qui respecte les interfaces de base.py.

À vérifier pour chaque fournisseur réel : le format exact de l'édition d'image
avec plusieurs références (ici : multipart `image[]`, comme l'API Images d'OpenAI)."""
import asyncio
import base64
import json

import httpx

from app.providers.base import (
    ContentBlocked,
    ImageResult,
    ProviderError,
    TextResult,
    Usage,
)

RETRIES = 5


class _Client:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def post(self, path: str, **kwargs) -> dict:
        """POST avec reprise sur 429 et 5xx (attente exponentielle)."""
        async with httpx.AsyncClient(timeout=300) as client:
            for attempt in range(RETRIES):
                res = await client.post(f"{self.base_url}{path}", headers=self.headers, **kwargs)
                if res.is_success:
                    return res.json()
                body = res.text[:500]
                if "content_policy" in body or "safety" in body.lower():
                    raise ContentBlocked(body)
                if res.status_code not in (429, 500, 502, 503, 504) or attempt == RETRIES - 1:
                    raise ProviderError(f"{res.status_code}: {body}")
                await asyncio.sleep(float(res.headers.get("retry-after") or 2**attempt))
        raise ProviderError("aucune réponse")


class OpenAICompatText(_Client):
    name = "openai_compat"

    async def json(self, *, model, system, user, schema, schema_name, images=None, max_tokens=16000) -> TextResult:
        content: list[dict] | str = user
        if images:
            content = [{"type": "text", "text": user}] + [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{base64.b64encode(data).decode()}"}}
                for data, mime in images
            ]
        body = await self.post("/chat/completions", json={
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}],
            "response_format": {"type": "json_schema", "json_schema": {"name": schema_name, "schema": schema, "strict": True}},
            "max_completion_tokens": max_tokens,
        })
        message = body["choices"][0]["message"]
        if not message.get("content"):
            if message.get("refusal"):
                raise ContentBlocked(message["refusal"])
            raise ProviderError("réponse vide")
        try:
            data = json.loads(message["content"])
        except json.JSONDecodeError as e:
            raise ProviderError(f"JSON illisible : {e}") from e
        u = body.get("usage") or {}
        return TextResult(data, Usage(u.get("prompt_tokens", 0), u.get("completion_tokens", 0)))


class OpenAICompatImage(_Client):
    name = "openai_compat"

    async def draw(self, *, model, prompt, references, size="1024x1536") -> ImageResult:
        if references:
            files = [("image[]", (f"ref{i}", data, mime)) for i, (data, mime) in enumerate(references)]
            body = await self.post("/images/edits", data={"model": model, "prompt": prompt, "size": size, "n": "1"}, files=files)
        else:
            body = await self.post("/images/generations", json={"model": model, "prompt": prompt, "size": size, "n": 1})
        item = body["data"][0]
        if item.get("b64_json"):
            return ImageResult(base64.b64decode(item["b64_json"]), "image/png")
        async with httpx.AsyncClient(timeout=120) as client:   # certains fournisseurs renvoient une URL
            res = await client.get(item["url"])
            res.raise_for_status()
            return ImageResult(res.content, res.headers.get("content-type", "image/png").split(";")[0])
