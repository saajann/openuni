from __future__ import annotations

from app.core.config import Settings


def test_cors_origins_accepts_comma_separated_env(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, https://foo.edu")

    settings = Settings()

    assert settings.cors_origins == ["http://localhost:3000", "https://foo.edu"]


def test_cors_origins_accepts_json_env(monkeypatch) -> None:
    monkeypatch.setenv(
        "CORS_ORIGINS",
        '["http://localhost:3000", "https://foo.edu"]',
    )

    settings = Settings()

    assert settings.cors_origins == ["http://localhost:3000", "https://foo.edu"]
