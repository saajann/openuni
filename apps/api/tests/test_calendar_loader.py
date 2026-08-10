from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml

from app.core import universities
from app.core.calendar import load_calendar_entries
from app.core.config import get_settings


@pytest.fixture
def temp_universities_dir(tmp_path: Path) -> Iterator[Path]:
    """Create a temporary universities directory and patch app settings."""
    settings = get_settings()
    original_dir = settings.universities_dir

    settings.universities_dir = tmp_path
    universities.load_universities()

    yield tmp_path

    settings.universities_dir = original_dir
    universities.load_universities()


def _write_demo_university(base_dir: Path) -> Path:
    demo_dir = base_dir / "demo"
    demo_dir.mkdir()

    config_data = {
        "slug": "demo",
        "name": "Demo University",
        "locale": "en",
        "domain": "example.edu",
        "qdrant_collection": "demo_collection",
        "sources": [],
    }

    with open(demo_dir / "config.yaml", "w", encoding="utf-8") as file:
        yaml.safe_dump(config_data, file)

    universities.load_universities()
    return demo_dir


def test_load_calendar_entries_returns_entries(temp_universities_dir: Path) -> None:
    demo_dir = _write_demo_university(temp_universities_dir)

    calendar_data = [
        {
            "type": "event",
            "title": "Orientation",
            "date": "2026-09-05",
            "description": "Welcome event for new students.",
        },
        {
            "type": "deadline",
            "title": "Tuition payment due",
            "date": "2026-09-01",
        },
    ]

    with open(demo_dir / "calendar.yaml", "w", encoding="utf-8") as file:
        yaml.safe_dump(calendar_data, file)

    entries = load_calendar_entries("demo")

    assert len(entries) == 2
    assert entries[0].type == "event"
    assert entries[0].title == "Orientation"
    assert entries[1].type == "deadline"
    assert entries[1].title == "Tuition payment due"


def test_missing_calendar_returns_empty_list(temp_universities_dir: Path) -> None:
    _write_demo_university(temp_universities_dir)

    assert load_calendar_entries("demo") == []


def test_invalid_yaml_raises_value_error(temp_universities_dir: Path) -> None:
    demo_dir = _write_demo_university(temp_universities_dir)
    with open(demo_dir / "calendar.yaml", "w", encoding="utf-8") as file:
        file.write("- type: event\n  title: Missing quote\n  date: [2026-09-05\n")

    with pytest.raises(ValueError, match="Invalid YAML"):
        load_calendar_entries("demo")


def test_invalid_entry_raises_value_error(temp_universities_dir: Path) -> None:
    demo_dir = _write_demo_university(temp_universities_dir)
    calendar_data = [
        {
            "type": "event",
            "title": "Orientation",
            "date": "2026-09-05",
            "end_date": "2026-09-01",
        }
    ]

    with open(demo_dir / "calendar.yaml", "w", encoding="utf-8") as file:
        yaml.safe_dump(calendar_data, file)

    with pytest.raises(ValueError, match="Invalid calendar entry"):
        load_calendar_entries("demo")


def test_unknown_slug_raises_key_error(temp_universities_dir: Path) -> None:
    with pytest.raises(KeyError):
        load_calendar_entries("unknown-slug")
