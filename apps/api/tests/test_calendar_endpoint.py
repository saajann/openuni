"""
tests/test_calendar_endpoint.py
───────────────────────────────
Integration tests for GET /universities/{slug}/calendar.

Calendar data is written to a temporary universities directory, so tests run
without touching the real `universities/` folder.  The TestClient drives the
real FastAPI routing, validation, and exception handling.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app.core import universities
from app.core.config import get_settings
from app.main import app

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def demo_university(tmp_path: Path) -> Iterator[Path]:
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

    yield demo_dir

    settings.universities_dir = original_dir
    universities.load_universities()


@pytest.fixture()
def demo_calendar(demo_university: Path) -> list[dict]:
    """Write a representative calendar.yaml for the temporary demo university."""
    calendar_data = [
        {
            "type": "exam",
            "title": "Exam registration window",
            "date": "2026-06-01",
            "end_date": "2026-06-10",
        },
        {
            "type": "deadline",
            "title": "Tuition payment deadline",
            "date": "2026-09-01",
        },
        {
            "type": "holiday",
            "title": "Christmas holiday",
            "date": "2026-12-25",
        },
        {
            "type": "event",
            "title": "Freshers' Orientation",
            "date": "2026-09-05",
        },
    ]
    with open(demo_university / "calendar.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(calendar_data, f)
    return calendar_data


# ── GET /universities/{slug}/calendar — happy path ────────────────────────────


def test_calendar_returns_all_entries(client: TestClient, demo_calendar: list[dict]) -> None:
    """A known university with a calendar returns every entry."""
    response = client.get("/universities/demo/calendar")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    assert {entry["type"] for entry in data} == {"exam", "deadline", "holiday", "event"}
    assert data[0]["title"] == "Exam registration window"
    assert data[0]["end_date"] == "2026-06-10"


def test_calendar_missing_file_returns_empty_list(
    client: TestClient, demo_university: Path
) -> None:
    """A known university without a calendar.yaml returns an empty list."""
    response = client.get("/universities/demo/calendar")

    assert response.status_code == 200
    assert response.json() == []


# ── Unknown university → 404 ──────────────────────────────────────────────────


def test_calendar_unknown_university_returns_404(
    client: TestClient, demo_calendar: list[dict]
) -> None:
    """An unrecognised slug must yield HTTP 404."""
    response = client.get("/universities/nonexistent-uni/calendar")

    assert response.status_code == 404
    assert "nonexistent-uni" in response.json()["detail"]


# ── ?type= filtering ──────────────────────────────────────────────────────────


def test_calendar_type_filter(client: TestClient, demo_calendar: list[dict]) -> None:
    """?type=deadline returns only deadline entries."""
    response = client.get("/universities/demo/calendar", params={"type": "deadline"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["type"] == "deadline"
    assert data[0]["title"] == "Tuition payment deadline"


def test_calendar_invalid_type_returns_422(client: TestClient, demo_calendar: list[dict]) -> None:
    """A type outside exam/deadline/holiday/event must yield HTTP 422."""
    response = client.get("/universities/demo/calendar", params={"type": "party"})

    assert response.status_code == 422


# ── ?from= / ?to= filtering ───────────────────────────────────────────────────


def test_calendar_from_filter(client: TestClient, demo_calendar: list[dict]) -> None:
    """?from= drops entries that end before the bound."""
    response = client.get("/universities/demo/calendar", params={"from": "2026-09-01"})

    assert response.status_code == 200
    titles = [entry["title"] for entry in response.json()]
    assert titles == ["Tuition payment deadline", "Christmas holiday", "Freshers' Orientation"]


def test_calendar_to_filter(client: TestClient, demo_calendar: list[dict]) -> None:
    """?to= drops entries that start after the bound."""
    response = client.get("/universities/demo/calendar", params={"to": "2026-09-01"})

    assert response.status_code == 200
    titles = [entry["title"] for entry in response.json()]
    assert titles == ["Exam registration window", "Tuition payment deadline"]


def test_calendar_range_overlaps_multi_day_entry(
    client: TestClient, demo_calendar: list[dict]
) -> None:
    """A from/to window inside a multi-day entry still matches that entry."""
    response = client.get(
        "/universities/demo/calendar",
        params={"from": "2026-06-05", "to": "2026-06-06"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Exam registration window"


def test_calendar_invalid_date_returns_422(client: TestClient, demo_calendar: list[dict]) -> None:
    """A malformed date bound must yield HTTP 422."""
    response = client.get("/universities/demo/calendar", params={"from": "not-a-date"})

    assert response.status_code == 422
