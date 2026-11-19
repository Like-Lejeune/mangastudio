"""Adaptateur Muse : forme des requêtes et lecture des réponses, sur un faux serveur."""
import base64
import json

import httpx
import pytest

from app.providers.base import ContentBlocked, ProviderError
from app.providers.meta_muse import MuseImage, MuseText

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 20


def server(handler):
    seen = []

    def wrapped(request: httpx.Request) -> httpx.Response:
        seen.append((request.url.path, json.loads(request.content), request.headers.get("authorization")))
        return handler(request, len(seen))
    return httpx.MockTransport(wrapped), seen


async def test_text_json_with_vision():
    reply = {"choices": [{"message": {"content": '```json\n{"look": "cheveux courts"}\n```'}}], "usage": {"prompt_tokens": 1200, "completion_tokens": 40}}
    transport, seen = server(lambda r, n: httpx.Response(200, json=reply))
    res = await MuseText("https://meta.test/v1", "cle", transport).json(
        model="muse-spark-1.3", system="s", user="u", schema={"type": "object"}, schema_name="design", images=[(PNG, "image/png")])
    path, body, auth = seen[0]
    assert path == "/v1/chat/completions" and auth == "Bearer cle"
    assert body["response_format"]["json_schema"]["strict"] is True and body["reasoning_effort"] == "low"
    assert body["messages"][1]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert res.data == {"look": "cheveux courts"} and (res.usage.input_tokens, res.usage.output_tokens) == (1200, 40)


async def test_image_edit_sends_references_and_drops_size_once():
    def handler(request, n):
        if n == 1:
            return httpx.Response(400, json={"error": {"type": "invalid_request_error", "param": "size", "message": "size is not supported"}})
        return httpx.Response(200, json={"data": [{"b64_json": base64.b64encode(PNG).decode()}]})
    transport, seen = server(handler)
    res = await MuseImage("https://meta.test/v1", "cle", transport).draw(
        model="muse-image-1.0", prompt="page 1", references=[(PNG, "image/png")] * 12)
    assert [p for p, _, _ in seen] == ["/v1/images/edits", "/v1/images/edits"]
    assert len(seen[0][1]["images"]) == 10 and "size" in seen[0][1] and "size" not in seen[1][1]
    assert res.image == PNG and res.mime == "image/png" and res.usage.images == 1


async def test_image_generation_without_reference():
    transport, seen = server(lambda r, n: httpx.Response(200, json={"data": [{"b64_json": base64.b64encode(PNG).decode()}]}))
    await MuseImage("https://meta.test/v1", "cle", transport).draw(model="muse-image-1.0", prompt="fiche", references=[], size="1536x1024")
    assert seen[0][0] == "/v1/images/generations" and seen[0][1]["size"] == "1536x1024"


async def test_errors():
    blocked, _ = server(lambda r, n: httpx.Response(400, json={"error": {"type": "content_policy_violation", "message": "refusé"}}))
    with pytest.raises(ContentBlocked):
        await MuseImage("https://meta.test/v1", "cle", blocked).draw(model="m", prompt="p", references=[])
    denied, seen = server(lambda r, n: httpx.Response(401, json={"error": {"type": "auth", "message": "clé invalide"}}))
    with pytest.raises(ProviderError, match="401"):
        await MuseText("https://meta.test/v1", "cle", denied).json(model="m", system="s", user="u", schema={}, schema_name="x")
    assert len(seen) == 1     # une erreur de clé n'est pas retentée
