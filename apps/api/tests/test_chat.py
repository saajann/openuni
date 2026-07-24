"""
tests/test_chat.py
──────────────────
Integration tests for POST /chat.

All external I/O (retrieve_chunks, generate_answer) is mocked so tests run
without a live Qdrant instance, Ollama, or OpenAI key.  The TestClient drives
the real FastAPI routing, validation, and exception handling.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from fastapi.testclient import TestClient

from app.core import universities
from app.core.config import get_settings
from app.main import app
from app.rag.generation import GeneratedAnswer
from app.rag.generation import CitedSource
from app.rag.retrieval import RetrievedChunk


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

    mock_retrieve.assert_called_once_with(
        university_slug="demo", question="How much is tuition?"
    )
    mock_generate.assert_called_once()


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


# ── POST /chat — missing required fields → 422 ───────────────────────────────


def test_chat_missing_university_slug_returns_422(client: TestClient) -> None:
    """Omitting university_slug entirely yields 422 (Pydantic validation)."""
    response = client.post("/chat", json={"question": "Any question?"})
    assert response.status_code == 422


def test_chat_missing_question_returns_422(client: TestClient) -> None:
    """Omitting question entirely yields 422 (Pydantic validation)."""
    response = client.post("/chat", json={"university_slug": "demo"})
    assert response.status_code == 422
