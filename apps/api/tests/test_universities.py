from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app.core import universities
from app.core.config import get_settings
from app.main import app


@pytest.fixture
def temp_universities_dir(tmp_path: Path) -> Iterator[Path]:
    """Fixture to create a temporary universities directory and patch settings."""
    settings = get_settings()
    original_dir = settings.universities_dir

    settings.universities_dir = tmp_path

    yield tmp_path

    # Restore original settings
    settings.universities_dir = original_dir


def test_valid_config_loads_correctly(temp_universities_dir: Path) -> None:
    # Setup valid demo university
    demo_dir = temp_universities_dir / "demo"
    demo_dir.mkdir()

    config_data = {
        "slug": "demo",
        "name": "Demo University",
        "locale": "en",
        "domain": "example.edu",
        "qdrant_collection": "demo_collection",
        "sources": ["source1.pdf"],
    }

    with open(demo_dir / "config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)

    universities.load_universities()

    all_unis = universities.list_universities()
    assert len(all_unis) == 1

    uni = universities.get_university("demo")
    assert uni.slug == "demo"
    assert uni.name == "Demo University"


def test_invalid_config_raises_error(temp_universities_dir: Path) -> None:
    # Setup invalid demo university (missing required fields)
    demo_dir = temp_universities_dir / "demo"
    demo_dir.mkdir()

    config_data = {
        "slug": "demo",
        "name": "Demo University",
        # missing locale, qdrant_collection, sources
    }

    with open(demo_dir / "config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)

    with pytest.raises(ValueError, match="Invalid configuration"):
        universities.load_universities()


def test_missing_config_skipped(temp_universities_dir: Path) -> None:
    # Setup a directory without a config.yaml
    empty_dir = temp_universities_dir / "empty"
    empty_dir.mkdir()

    # Also create a valid one to make sure it still loads
    demo_dir = temp_universities_dir / "demo"
    demo_dir.mkdir()
    config_data = {
        "slug": "demo",
        "name": "Demo University",
        "locale": "en",
        "domain": "example.edu",
        "qdrant_collection": "demo",
        "sources": [],
    }
    with open(demo_dir / "config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)

    universities.load_universities()

    all_unis = universities.list_universities()
    assert len(all_unis) == 1
    assert all_unis[0].slug == "demo"


def test_slug_mismatch_raises_error(temp_universities_dir: Path) -> None:
    # Setup a directory with a mismatched slug
    demo_dir = temp_universities_dir / "demo_folder"
    demo_dir.mkdir()

    config_data = {
        "slug": "wrong_slug",
        "name": "Demo University",
        "locale": "en",
        "domain": "example.edu",
        "qdrant_collection": "demo_collection",
        "sources": [],
    }

    with open(demo_dir / "config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)

    with pytest.raises(ValueError, match="does not match folder name"):
        universities.load_universities()


def test_get_universities_endpoint(temp_universities_dir: Path) -> None:
    # Setup valid demo university
    demo_dir = temp_universities_dir / "demo"
    demo_dir.mkdir()
    config_data = {
        "slug": "demo",
        "name": "Demo University",
        "locale": "en",
        "domain": "example.edu",
        "qdrant_collection": "demo_collection",
        "sources": [],
    }
    with open(demo_dir / "config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)

    # Reload universities into the registry
    universities.load_universities()

    client = TestClient(app)
    response = client.get("/universities")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["slug"] == "demo"
    assert data[0]["name"] == "Demo University"
    assert data[0]["locale"] == "en"
    assert data[0]["domain"] == "example.edu"
    # Ensure no internal fields like qdrant_collection or sources are present
    assert "qdrant_collection" not in data[0]
    assert "sources" not in data[0]
