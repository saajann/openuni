"""
tests/test_chat.py
──────────────────
Integration tests for POST /chat.

All external I/O (retrieve_chunks, generate_answer) is mocked so tests run
without a live Qdrant instance, Ollama, or OpenAI key.  The TestClient drives
the real FastAPI routing, validation, and exception handling.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.core import universities
from app.core.config import get_settings
from app.main import app
from app.rag.generation import (
    CitedSource,
    GeneratedAnswer,
    LLMProviderUnavailable,
)
from app.rag.retrieval import RetrievalUnavailable, RetrievedChunk

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def demo_university(tmp_path: Path) -> Iterator[None]:
    """Load a minimal 'demo' university into the registry for the duration of the test."""
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


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_chunk(text: str, source: str) -> RetrievedChunk:
    return RetrievedChunk(chunk_text=text, source=source, score=0.95)


def _make_generated(answer: str, sources: list[tuple[str, str]]) -> GeneratedAnswer:
    return GeneratedAnswer(
        answer=answer,
        sources=[CitedSource(text_snippet=snip, source=src) for snip, src in sources],
    )


# ── POST /chat — happy path ───────────────────────────────────────────────────


def test_chat_valid_question_returns_grounded_answer(
    client: TestClient, demo_university: None
) -> None:
    """A real question for a known university returns answer + sources."""
    chunks = [_make_chunk("Tuition is €3 000 per year.", "fees.pdf")]
    generated = _make_generated(
        answer="Tuition is €3 000 per year [1].",
        sources=[("Tuition is €3 000 per year.", "fees.pdf")],
    )

    with (
        patch("app.routers.chat.retrieve_chunks", return_value=chunks) as mock_retrieve,
        patch("app.routers.chat.generate_answer", return_value=generated) as mock_generate,
    ):
        response = client.post(
            "/chat",
            json={"university_slug": "demo", "question": "How much is tuition?"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "€3 000" in data["answer"]
    assert len(data["sources"]) == 1
    assert data["sources"][0]["source"] == "fees.pdf"
    assert data["sources"][0]["text_snippet"] == "Tuition is €3 000 per year."

    mock_retrieve.assert_called_once_with(university_slug="demo", question="How much is tuition?")
    mock_generate.assert_called_once()


# ── POST /chat — concurrency ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chat_does_not_block_the_event_loop_during_retrieval(
    demo_university: None,
) -> None:
    """A slow retrieval runs in a worker thread, so /health stays responsive.

    If ``retrieve_chunks`` were called directly from the async handler, the
    event loop would be blocked inside the sync function and this test would
    deadlock until the delayed release (or fail because the chat request
    completed before /health could be served).
    """
    retrieval_started = threading.Event()
    release_retrieval = threading.Event()

    def slow_retrieve(*, university_slug: str, question: str) -> list[RetrievedChunk]:
        retrieval_started.set()
        release_retrieval.wait(timeout=5.0)
        return []

    transport = ASGITransport(app=app)

    with patch("app.routers.chat.retrieve_chunks", side_effect=slow_retrieve):
        async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
            chat_request = asyncio.create_task(
                async_client.post(
                    "/chat",
                    json={"university_slug": "demo", "question": "When is the exam?"},
                )
            )
            try:
                assert await asyncio.to_thread(retrieval_started.wait, 2.0)
                # While the worker thread is blocked, the chat request must
                # still be pending and unrelated endpoints must respond.
                assert not chat_request.done()
                health_response = await asyncio.wait_for(async_client.get("/health"), timeout=2.0)
                assert health_response.status_code == 200
                assert not chat_request.done()
            finally:
                release_retrieval.set()

            chat_response = await asyncio.wait_for(chat_request, timeout=5.0)

    assert chat_response.status_code == 200
    assert chat_response.json()["sources"] == []


# ── POST /chat — invalid university → 404 ────────────────────────────────────


def test_chat_unknown_university_returns_404(client: TestClient, demo_university: None) -> None:
    """An unrecognised university_slug must yield HTTP 404."""
    response = client.post(
        "/chat",
        json={"university_slug": "nonexistent-uni", "question": "What are the fees?"},
    )

    assert response.status_code == 404
    assert "nonexistent-uni" in response.json()["detail"]


# ── POST /chat — empty question → 422 ────────────────────────────────────────


def test_chat_empty_question_returns_422(client: TestClient, demo_university: None) -> None:
    """An empty question string must yield HTTP 422."""
    response = client.post(
        "/chat",
        json={"university_slug": "demo", "question": ""},
    )

    assert response.status_code == 422


def test_chat_whitespace_only_question_returns_422(
    client: TestClient, demo_university: None
) -> None:
    """A whitespace-only question must also yield HTTP 422."""
    response = client.post(
        "/chat",
        json={"university_slug": "demo", "question": "   "},
    )

    assert response.status_code == 422


# ── POST /chat — no matching content → fallback answer ───────────────────────


def test_chat_no_matching_content_returns_fallback(
    client: TestClient, demo_university: None
) -> None:
    """When retrieve_chunks returns nothing, generation returns the fallback answer."""
    from app.rag.generation import _NO_INFORMATION_ANSWER

    fallback = _make_generated(answer=_NO_INFORMATION_ANSWER, sources=[])

    with (
        patch("app.routers.chat.retrieve_chunks", return_value=[]),
        patch("app.routers.chat.generate_answer", return_value=fallback),
    ):
        response = client.post(
            "/chat",
            json={"university_slug": "demo", "question": "What is the moon made of?"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == _NO_INFORMATION_ANSWER
    assert data["sources"] == []


# ── POST /chat — provider outage → 503 ───────────────────────────────────────


def test_chat_provider_unavailable_returns_503(client: TestClient, demo_university: None) -> None:
    """A provider outage maps to a stable, non-leaking 503 response."""
    chunks = [_make_chunk("Fees are listed in the handbook.", "fees.pdf")]

    with (
        patch("app.routers.chat.retrieve_chunks", return_value=chunks),
        patch(
            "app.routers.chat.generate_answer",
            side_effect=LLMProviderUnavailable("sk-secret: provider exploded"),
        ),
    ):
        response = client.post(
            "/chat",
            json={"university_slug": "demo", "question": "How much is tuition?"},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Answer generation is temporarily unavailable. Please try again shortly."
    )
    assert "sk-secret" not in response.text
    assert "provider exploded" not in response.text


def test_chat_retrieval_unavailable_returns_503(client: TestClient, demo_university: None) -> None:
    """A retrieval outage maps to a stable, non-leaking 503 response."""
    with patch(
        "app.routers.chat.retrieve_chunks",
        side_effect=RetrievalUnavailable("qdrant token abc leaked detail"),
    ):
        response = client.post(
            "/chat",
            json={"university_slug": "demo", "question": "How much is tuition?"},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Retrieval is temporarily unavailable. Please try again shortly."
    )
    assert "qdrant token" not in response.text
    assert "leaked detail" not in response.text


def test_chat_unexpected_generation_error_returns_500(
    client: TestClient, demo_university: None
) -> None:
    """Programming errors are not disguised as provider outages."""
    chunks = [_make_chunk("Fees are listed in the handbook.", "fees.pdf")]
    error_client = TestClient(app, raise_server_exceptions=False)

    with (
        patch("app.routers.chat.retrieve_chunks", return_value=chunks),
        patch("app.routers.chat.generate_answer", side_effect=RuntimeError("boom")),
    ):
        response = error_client.post(
            "/chat",
            json={"university_slug": "demo", "question": "How much is tuition?"},
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
    assert "boom" not in response.text


# ── POST /chat — missing required fields → 422 ───────────────────────────────


def test_chat_missing_university_slug_returns_422(client: TestClient) -> None:
    """Omitting university_slug entirely yields 422 (Pydantic validation)."""
    response = client.post("/chat", json={"question": "Any question?"})
    assert response.status_code == 422


def test_chat_missing_question_returns_422(client: TestClient) -> None:
    """Omitting question entirely yields 422 (Pydantic validation)."""
    response = client.post("/chat", json={"university_slug": "demo"})
    assert response.status_code == 422


# ── OPTIONS /chat — CORS preflight ─────────────────────────────────────


def test_options_chat_preflight_is_allowed(client: TestClient) -> None:
    """The OPTIONS /chat preflight must return 200 so browsers can
    send the actual POST /chat request (fixes #31)."""
    response = client.options(
        "/chat",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
