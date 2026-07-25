"""
tests/test_cors.py
───────────────────
Regression tests for CORS headers, including on error responses.

CORSMiddleware alone does not reliably add CORS headers to responses built
by a top-level `@app.exception_handler(Exception)` handler (a documented
Starlette gotcha: browsers may treat the response as CORS-blocked even
though the middleware is installed). Without the explicit header-setting in
that handler, a browser-based frontend hitting a real server error would see
an opaque "blocked by CORS policy" failure instead of the actual error.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from fastapi.testclient import TestClient

from app.core import universities
from app.core.config import get_settings
from app.main import app

ALLOWED_ORIGIN = "http://localhost:3000"


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def demo_university(tmp_path: Path) -> Iterator[None]:
    settings = get_settings()
    original_dir = settings.universities_dir
    settings.universities_dir = tmp_path
    demo_dir = tmp_path / "demo"
    demo_dir.mkdir()

    config_data = {
        "slug": "demo",
        "name": "Demo University",
        "locale": "en",
        "domain": "demo.edu",
        "qdrant_collection": "demo_collection",
        "sources": ["handbook.pdf"],
    }
    with open(demo_dir / "config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)

    universities.load_universities()

    yield

    settings.universities_dir = original_dir
    universities.load_universities()


def test_cors_header_present_on_success_response(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": ALLOWED_ORIGIN})

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN


def test_cors_header_present_on_unhandled_exception_response(demo_university: None) -> None:
    """A browser-facing request that hits the global exception handler must
    still get CORS headers, or the browser hides the real error behind an
    opaque CORS failure instead.

    Uses raise_server_exceptions=False: by default TestClient re-raises the
    underlying exception instead of returning the app's actual 500 response,
    which is what we need to inspect here (this mirrors what a real deployed
    server does for a client, since there's no test runner to re-raise into).
    """
    client = TestClient(app, raise_server_exceptions=False)
    with patch("app.routers.chat.retrieve_chunks", side_effect=RuntimeError("boom")):
        response = client.post(
            "/chat",
            json={"university_slug": "demo", "question": "When is the deadline?"},
            headers={"Origin": ALLOWED_ORIGIN},
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert response.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN


def test_cors_header_absent_for_disallowed_origin(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "https://not-allowed.example.com"})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
