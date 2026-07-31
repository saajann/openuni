"""Integration tests for GET /ready with all external services mocked."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.main import app


def _http_probe_client(*, ollama_error: Exception | None = None) -> AsyncMock:
    client = AsyncMock()
    client.__aenter__.return_value = client
    qdrant_response = MagicMock()
    ollama_response = MagicMock()
    client.get.side_effect = [
        qdrant_response,
        ollama_error if ollama_error is not None else ollama_response,
    ]
    return client


@pytest.mark.asyncio
async def test_ready_includes_ollama_when_all_dependencies_are_reachable() -> None:
    connection = AsyncMock()
    probes = _http_probe_client()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        with (
            patch(
                "app.main.psycopg.AsyncConnection.connect",
                new=AsyncMock(return_value=connection),
            ),
            patch("app.main.httpx.AsyncClient", return_value=probes),
        ):
            response = await client.get("/ready")

    assert response.status_code == 200
    assert response.json()["checks"] == {
        "postgres": "ok",
        "qdrant": "ok",
        "ollama": "ok",
    }
    assert probes.get.await_args_list[1].args[0].endswith("/api/tags")


@pytest.mark.asyncio
async def test_ready_is_degraded_when_ollama_is_unreachable() -> None:
    connection = AsyncMock()
    probes = _http_probe_client(ollama_error=httpx.ConnectError("connection refused"))
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        with (
            patch(
                "app.main.psycopg.AsyncConnection.connect",
                new=AsyncMock(return_value=connection),
            ),
            patch("app.main.httpx.AsyncClient", return_value=probes),
        ):
            response = await client.get("/ready")

    body = response.json()
    assert response.status_code == 503
    assert body["status"] == "degraded"
    assert body["checks"]["postgres"] == "ok"
    assert body["checks"]["qdrant"] == "ok"
    assert body["checks"]["ollama"] == "error: connection refused"
