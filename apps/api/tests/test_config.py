from __future__ import annotations

import pytest

from app.core.config import Settings


def test_cors_origins_accepts_comma_separated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, https://foo.edu")

    settings = Settings()

    assert settings.cors_origins == ["http://localhost:3000", "https://foo.edu"]


def test_cors_origins_accepts_json_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "CORS_ORIGINS",
        '["http://localhost:3000", "https://foo.edu"]',
    )

    settings = Settings()

    assert settings.cors_origins == ["http://localhost:3000", "https://foo.edu"]


def test_ollama_generation_model_has_a_lightweight_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)

    settings = Settings()

    assert settings.ollama_model == "qwen2.5:0.5b"
