"""Transport adapter used only for explicitly configured destinations/tests."""
from __future__ import annotations

import httpx


class WebhookNotifier:
    def __init__(self, authorized_url: str):
        self.url = authorized_url

    def send(self, payload: dict) -> dict:
        response = httpx.post(self.url, json=payload, timeout=5, follow_redirects=False)
        response.raise_for_status()
        return {"status": "ENDPOINT_ACCEPTED", "http_status": response.status_code}
