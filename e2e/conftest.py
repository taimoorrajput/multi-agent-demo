"""E2E harness: starts the real FastAPI app with uvicorn on a free port, then drives Swagger UI.

Run with video (this is the "recorded feature run" for the merge gate):
    uv run pytest e2e -k T001 --video on --output .agents/evidence/T-001/playwright

Each run picks its own free port, so parallel builders don't clash on :8000.
Requires: pytest-playwright (`uv add --dev pytest-playwright && uv run playwright install chromium`)
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time

import httpx
import pytest
from playwright.sync_api import Page, expect

APP_MODULE = os.getenv("APP_MODULE", "app.main:app")


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def base_url() -> str:  # overrides pytest-base-url's fixture used by Playwright's `page`
    port = _free_port()
    env = {**os.environ, "ENV": os.getenv("ENV", "test")}
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", APP_MODULE, "--host", "127.0.0.1", "--port", str(port)],
        env=env,
    )
    url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            if httpx.get(f"{url}/openapi.json", timeout=1).status_code == 200:
                break
        except httpx.HTTPError:
            pass
        if proc.poll() is not None:
            raise RuntimeError(f"uvicorn exited early with code {proc.returncode}")
        time.sleep(0.3)
    else:
        proc.terminate()
        raise RuntimeError("API did not start within 30s")
    yield url
    proc.terminate()
    proc.wait(timeout=10)


class Swagger:
    """Clicks through Swagger UI (/docs) so the video shows the feature working."""

    def __init__(self, page: Page, base_url: str):
        self.page, self.base_url = page, base_url

    def open(self) -> None:
        self.page.goto(f"{self.base_url}/docs")
        expect(self.page.locator(".swagger-ui")).to_be_visible()

    def call(self, method: str, path: str, body: str | None = None,
             params: dict[str, str] | None = None, expect_status: int = 200) -> str:
        """Expand an operation, Try it out, fill params/body, Execute, assert status. Returns response body text."""
        op = self.page.locator(f".opblock-{method.lower()}").filter(
            has=self.page.locator(f'[data-path="{path}"]')
        ).first
        op.locator(".opblock-summary").click()
        op.get_by_role("button", name="Try it out").click()
        for name, value in (params or {}).items():
            op.locator(f'tr[data-param-name="{name}"] input').fill(value)
        if body is not None:
            op.locator("textarea.body-param__text").fill(body)
        op.get_by_role("button", name="Execute").click()
        status = op.locator(".live-responses-table .response .response-col_status").first
        expect(status).to_have_text(str(expect_status), timeout=10_000)
        self.page.wait_for_timeout(800)  # leave a beat on screen for the recording
        return op.locator(".live-responses-table .microlight").first.inner_text()


@pytest.fixture
def swagger(page: Page, base_url: str) -> Swagger:
    sw = Swagger(page, base_url)
    sw.open()
    return sw
