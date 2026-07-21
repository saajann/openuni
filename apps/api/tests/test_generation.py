"""
tests/test_generation.py
────────────────────────
Unit tests for ``app.rag.generation``.

All tests mock the OpenAI client so no live API key or network access is
needed.  The mock verifies:
  - Prompt structure (system + user messages, model, temperature, response
    format).
  - Correct parsing of the LLM JSON response into ``GeneratedAnswer``.
  - The empty-chunks short-circuit returns the fixed "no information" response
    without touching the LLM at all.
  - Graceful fallback when the LLM returns malformed JSON.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.rag.generation import (
    _NO_INFORMATION_ANSWER,
    _SYSTEM_PROMPT,
    GeneratedAnswer,
    _build_user_message,
    _parse_llm_response,
    _resolve_client_and_model,
    generate_answer,
)
from app.rag.retrieval import RetrievedChunk

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_chunk(text: str, source: str, score: float = 0.9) -> RetrievedChunk:
    return RetrievedChunk(chunk_text=text, source=source, score=score)


def _fake_openai_response(content: str) -> MagicMock:
    """Build a minimal mock that mirrors openai.ChatCompletion structure."""
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


# ── _build_user_message ───────────────────────────────────────────────────────


def test_build_user_message_contains_question() -> None:
    chunks = [_make_chunk("Deadlines are in September.", "handbook.pdf")]
    msg = _build_user_message("When are deadlines?", chunks)
    assert "When are deadlines?" in msg


def test_build_user_message_includes_passage_index_and_source() -> None:
    chunks = [
        _make_chunk("Tuition is €3 000 per year.", "fees.pdf"),
        _make_chunk("Apply before 1 March.", "admissions.html"),
    ]
    msg = _build_user_message("How much does it cost?", chunks)
    assert "Passage [1]" in msg
    assert "source: fees.pdf" in msg
    assert "Passage [2]" in msg
    assert "source: admissions.html" in msg


def test_build_user_message_unknown_source_when_none() -> None:
    chunk = RetrievedChunk(chunk_text="Some info.", source=None, score=0.5)
    msg = _build_user_message("Any info?", [chunk])
    assert "source: unknown" in msg


# ── _parse_llm_response ───────────────────────────────────────────────────────


def test_parse_llm_response_valid_json() -> None:
    payload: dict[str, Any] = {
        "answer": "Deadlines are in September [1].",
        "sources": [{"text_snippet": "Deadlines are in September.", "source": "handbook.pdf"}],
    }
    result = _parse_llm_response(json.dumps(payload))

    assert isinstance(result, GeneratedAnswer)
    assert result.answer == "Deadlines are in September [1]."
    assert len(result.sources) == 1
    assert result.sources[0].text_snippet == "Deadlines are in September."
    assert result.sources[0].source == "handbook.pdf"


def test_parse_llm_response_malformed_json_returns_raw_text() -> None:
    raw = "This is not JSON at all."
    result = _parse_llm_response(raw)
    assert result.answer == raw
    assert result.sources == []


def test_parse_llm_response_ignores_non_dict_source_items() -> None:
    payload: dict[str, Any] = {
        "answer": "Some answer.",
        "sources": [
            "bad_string_item",
            {"text_snippet": "Valid snippet.", "source": "doc.pdf"},
        ],
    }
    result = _parse_llm_response(json.dumps(payload))
    # Only the valid dict item should survive
    assert len(result.sources) == 1
    assert result.sources[0].source == "doc.pdf"


def test_parse_llm_response_empty_sources_list() -> None:
    payload: dict[str, Any] = {"answer": "No applicable sources.", "sources": []}
    result = _parse_llm_response(json.dumps(payload))
    assert result.sources == []


# ── generate_answer — empty chunks short-circuit ──────────────────────────────


def test_generate_answer_empty_chunks_returns_no_information() -> None:
    """No LLM call should be made when chunks is empty."""
    mock_client = MagicMock()

    result = generate_answer("What scholarships exist?", chunks=[], client=mock_client)

    mock_client.chat.completions.create.assert_not_called()
    assert result.answer == _NO_INFORMATION_ANSWER
    assert result.sources == []


# ── generate_answer — happy path with mocked LLM ─────────────────────────────


def test_generate_answer_calls_llm_with_correct_structure() -> None:
    """Verify the prompt shape and model parameters sent to the OpenAI client."""
    chunks = [
        _make_chunk("Applications open on 1 October.", "admissions.pdf"),
        _make_chunk("Late applications are not accepted.", "policy.pdf"),
    ]
    llm_payload: dict[str, Any] = {
        "answer": "Applications open on 1 October [1]. Late applications are not accepted [2].",
        "sources": [
            {"text_snippet": "Applications open on 1 October.", "source": "admissions.pdf"},
            {"text_snippet": "Late applications are not accepted.", "source": "policy.pdf"},
        ],
    }

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _fake_openai_response(
        json.dumps(llm_payload)
    )

    result = generate_answer(
        "When do applications open?",
        chunks=chunks,
        model="gpt-4o-mini",
        client=mock_client,
    )

    # ── Assert the LLM was called exactly once ────────────────────────────────
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs

    # Model
    assert call_kwargs["model"] == "gpt-4o-mini"

    # Temperature must be 0 (deterministic grounding)
    assert call_kwargs["temperature"] == 0.0

    # JSON mode enabled
    assert call_kwargs["response_format"] == {"type": "json_object"}

    # Messages: system + user
    messages = call_kwargs["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == _SYSTEM_PROMPT
    assert messages[1]["role"] == "user"

    user_content: str = messages[1]["content"]
    # Both passages and the question must be present
    assert "Applications open on 1 October." in user_content
    assert "Late applications are not accepted." in user_content
    assert "When do applications open?" in user_content
    assert "admissions.pdf" in user_content
    assert "policy.pdf" in user_content

    # ── Assert the parsed result ──────────────────────────────────────────────
    assert "1 October" in result.answer
    assert len(result.sources) == 2
    assert result.sources[0].source == "admissions.pdf"
    assert result.sources[1].source == "policy.pdf"


def test_generate_answer_uses_settings_model_by_default() -> None:
    """When no model is passed, the model comes from application settings."""
    chunks = [_make_chunk("Info.", "doc.pdf")]
    llm_payload: dict[str, Any] = {"answer": "Info.", "sources": []}

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _fake_openai_response(
        json.dumps(llm_payload)
    )

    with patch("app.rag.generation.get_settings") as mock_settings_fn:
        settings = MagicMock()
        settings.openai_model = "gpt-4o-mini"
        mock_settings_fn.return_value = settings

        generate_answer("Tell me about info.", chunks=chunks, client=mock_client)

    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o-mini"


# ── _resolve_client_and_model — provider resolution ───────────────────────────


def test_resolve_client_openai() -> None:
    """openai provider returns a vanilla OpenAI client and the openai_model."""
    settings = MagicMock()
    settings.llm_provider = "openai"
    settings.openai_api_key.get_secret_value.return_value = "sk-test"
    settings.openai_model = "gpt-4o-mini"

    with patch("app.rag.generation.OpenAI") as MockOpenAI:
        MockOpenAI.return_value = MagicMock()
        client, model = _resolve_client_and_model(settings)

    MockOpenAI.assert_called_once_with(api_key="sk-test")
    assert model == "gpt-4o-mini"


def test_resolve_client_ollama() -> None:
    """ollama provider returns an OpenAI client pointed at Ollama's /v1 endpoint."""
    settings = MagicMock()
    settings.llm_provider = "ollama"
    settings.ollama_url = "http://ollama:11434"
    settings.ollama_model = "llama3.1"

    with patch("app.rag.generation.OpenAI") as MockOpenAI:
        MockOpenAI.return_value = MagicMock()
        client, model = _resolve_client_and_model(settings)

    call_kwargs = MockOpenAI.call_args.kwargs
    assert call_kwargs["base_url"].endswith("/v1")
    assert "ollama:11434" in call_kwargs["base_url"]
    assert call_kwargs["api_key"] == "ollama"
    assert model == "llama3.1"


def test_resolve_client_invalid_provider_raises() -> None:
    """An unrecognised llm_provider raises ValueError with a helpful message."""
    settings = MagicMock()
    settings.llm_provider = "anthropic"

    with pytest.raises(ValueError, match="Unknown LLM_PROVIDER 'anthropic'"):
        _resolve_client_and_model(settings)


def test_generate_answer_ollama_provider_routes_to_ollama_client() -> None:
    """generate_answer() with llm_provider='ollama' uses an Ollama-backed client."""
    chunks = [_make_chunk("Term starts 1 September.", "calendar.pdf")]
    llm_payload: dict[str, Any] = {
        "answer": "Term starts 1 September [1].",
        "sources": [{"text_snippet": "Term starts 1 September.", "source": "calendar.pdf"}],
    }

    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create.return_value = _fake_openai_response(
        json.dumps(llm_payload)
    )

    with (
        patch("app.rag.generation.get_settings") as mock_settings_fn,
        patch("app.rag.generation.OpenAI", return_value=mock_client_instance) as MockOpenAI,
    ):
        settings = MagicMock()
        settings.llm_provider = "ollama"
        settings.ollama_url = "http://ollama:11434"
        settings.ollama_model = "llama3.1"
        mock_settings_fn.return_value = settings

        result = generate_answer("When does term start?", chunks=chunks)

    # Client must have been constructed for Ollama's /v1 endpoint
    call_kwargs = MockOpenAI.call_args.kwargs
    assert call_kwargs["base_url"].endswith("/v1")
    assert call_kwargs["api_key"] == "ollama"

    # Parsed result should be correct
    assert "1 September" in result.answer
    assert result.sources[0].source == "calendar.pdf"
