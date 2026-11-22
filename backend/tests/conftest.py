"""Base SQLite et stockage temporaires, fournisseurs factices : aucun appel réseau."""
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="mangastudio-")
os.environ.update({
    "DATABASE_URL": f"sqlite+aiosqlite:///{_tmp}/test.db",
    "STORAGE_DIR": f"{_tmp}/storage",
    "TRUSTCHANGE_API_KEY": "tc_test_cle",
    "TRUSTCHANGE_BASE_URL": "https://trustchange.invalid",
    "TRUSTCHANGE_WEBHOOK_SECRET": "secret-de-test",
    # Les tests existants créent des comptes et les utilisent aussitôt ; test_verification.py active la vérification.
    "EMAIL_VERIFICATION": "false",
    "PRICES": '{"fake-writer":{"in":4,"out":20},"fake-checker":{"in":1,"out":4},"fake-image":{"image":0.04}}',
})

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.db import init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest_asyncio.fixture(scope="session")
async def client():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture(autouse=True)
async def _sans_limite_de_tentatives():
    """Les tests créent beaucoup de comptes depuis la même adresse : compteurs remis à zéro à chaque test."""
    from app import ratelimit
    ratelimit.clear_all()
    yield
