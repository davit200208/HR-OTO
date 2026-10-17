from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class ProviderResult:
    success: bool
    provider_message_id: str = ""
    error: str = ""
    status: str = "sent"


class BrevoEmailAdapter:
    base_url = "https://api.brevo.com/v3"

    def __init__(self, api_key: str, timeout: int = 10, client: httpx.AsyncClient | None = None):
        self.api_key, self.timeout, self.client = api_key, timeout, client

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        headers = {"api-key": self.api_key, "accept": "application/json", **kwargs.pop("headers", {})}
        if self.client:
            return await self.client.request(method, self.base_url + path, headers=headers, timeout=self.timeout, **kwargs)
        async with httpx.AsyncClient() as client:
            return await client.request(method, self.base_url + path, headers=headers, timeout=self.timeout, **kwargs)

    async def test_connection(self) -> ProviderResult:
        response = await self._request("GET", "/account")
        return ProviderResult(response.is_success, error="Brevo rejected credentials" if not response.is_success else "", status="connected" if response.is_success else "failed")

    async def send_email(self, *, to: str, subject: str, html_content: str, sender_name: str, sender_email: str,
                         reply_to: str = "", template_id: int | None = None, params: dict | None = None,
                         idempotency_key: str = "") -> ProviderResult:
        body: dict[str, Any] = {"to": [{"email": to}], "subject": subject, "htmlContent": html_content,
                                "sender": {"name": sender_name, "email": sender_email}}
        if reply_to: body["replyTo"] = {"email": reply_to}
        if template_id is not None: body["templateId"] = template_id
        if params: body["params"] = params
        if idempotency_key: body["headers"] = {"Idempotency-Key": idempotency_key}
        response = await self._request("POST", "/smtp/email", json=body)
        data = response.json() if response.content else {}
        return ProviderResult(response.is_success, str(data.get("messageId", "")), "Brevo send failed" if not response.is_success else "", "sent" if response.is_success else "failed")


class SmsOfflineMockAdapter:
    """Safe default until SMSOffline supplies authoritative API documentation."""
    async def test_connection(self) -> ProviderResult:
        return ProviderResult(False, error="SMSOffline API documentation and credentials are not configured", status="not_configured")

    async def send_sms(self, **_: Any) -> ProviderResult:
        return ProviderResult(False, error="SMSOffline mock adapter: real provider endpoint is pending", status="not_configured")
