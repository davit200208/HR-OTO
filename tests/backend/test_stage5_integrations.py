import httpx
import asyncio
import json

from app.integrations.providers import BrevoEmailAdapter, SmsOfflineMockAdapter
from app.services.secrets import InMemorySecretStore, mask_secret


def test_brevo_adapter_uses_official_paths_and_api_key_header():
    asyncio.run(_test_brevo_adapter())

async def _test_brevo_adapter():
    requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/v3/account": return httpx.Response(200, json={"email": "owner@example.com"})
        return httpx.Response(201, json={"messageId": "brevo-1"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = BrevoEmailAdapter("secret-key-123", client=client)
        assert (await adapter.test_connection()).success
        sent = await adapter.send_email(to="a@example.com", subject="t", html_content="<p>x</p>", sender_name="HR", sender_email="hr@example.com", idempotency_key="id-1")
        assert sent.provider_message_id == "brevo-1"
    assert requests[0].url.path == "/v3/account"
    assert requests[0].headers["api-key"] == "secret-key-123"
    assert requests[1].url.path == "/v3/smtp/email"
    assert json.loads(requests[1].content)["headers"]["Idempotency-Key"] == "id-1"


def test_smsoffline_is_explicitly_not_configured_without_authoritative_docs():
    result = asyncio.run(SmsOfflineMockAdapter().test_connection())
    assert not result.success
    assert result.status == "not_configured"
    assert "documentation" in result.error


def test_secret_masking_never_returns_full_secret():
    secret = "brevo-super-secret"
    masked = mask_secret(secret)
    assert masked.endswith("cret")
    assert secret not in masked
    store = InMemorySecretStore()
    store.put("brevo", secret, 1)
    assert store.get("brevo") == secret
