from types import SimpleNamespace

import pytest
from qdrant_client.http import models

from ingestion.vector_store import qdrant


class FakeQdrantClient:
    def __init__(self, *, url: str) -> None:
        self.url = url
        self.collection_names: list[str] = []
        self.created_collections: list[dict] = []
        self.deleted: list[dict] = []
        self.upserted: list[dict] = []

    def get_collections(self) -> SimpleNamespace:
        return SimpleNamespace(
            collections=[SimpleNamespace(name=name) for name in self.collection_names]
        )

    def create_collection(self, **kwargs) -> None:
        self.created_collections.append(kwargs)

    def delete(self, **kwargs) -> None:
        self.deleted.append(kwargs)

    def upsert(self, **kwargs) -> None:
        self.upserted.append(kwargs)


@pytest.fixture
def store_and_client(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[qdrant.QdrantStore, FakeQdrantClient]:
    client = FakeQdrantClient(url="http://qdrant:6333")
    monkeypatch.setattr(qdrant, "QdrantClient", lambda **_: client)
    store = qdrant.QdrantStore(collection_name="universities", vector_size=384)
    return store, client


def test_init_creates_missing_collection(
    store_and_client: tuple[qdrant.QdrantStore, FakeQdrantClient],
) -> None:
    _, client = store_and_client

    assert len(client.created_collections) == 1
    call = client.created_collections[0]
    assert call["collection_name"] == "universities"
    assert call["vectors_config"].size == 384
    assert call["vectors_config"].distance == models.Distance.COSINE


def test_init_skips_creation_when_collection_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeQdrantClient(url="http://qdrant:6333")
    client.collection_names = ["universities"]
    monkeypatch.setattr(qdrant, "QdrantClient", lambda **_: client)

    qdrant.QdrantStore(collection_name="universities")

    assert client.created_collections == []


def test_delete_university_data_deletes_matching_points(
    store_and_client: tuple[qdrant.QdrantStore, FakeQdrantClient],
) -> None:
    store, client = store_and_client

    store.delete_university_data("stanford")

    assert len(client.deleted) == 1
    call = client.deleted[0]
    assert call["collection_name"] == "universities"
    condition = call["points_selector"].filter.must[0]
    assert condition.key == "university_slug"
    assert condition.match.value == "stanford"


def test_upsert_points_builds_point_structs(
    store_and_client: tuple[qdrant.QdrantStore, FakeQdrantClient],
) -> None:
    store, client = store_and_client
    vectors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    payloads = [{"university_slug": "stanford"}, {"university_slug": "mit"}]

    store.upsert_points(vectors, payloads)

    assert len(client.upserted) == 1
    call = client.upserted[0]
    assert call["collection_name"] == "universities"
    points = call["points"]
    assert len(points) == 2
    for point, vector, payload in zip(points, vectors, payloads, strict=True):
        assert isinstance(point.id, str)
        assert point.id
        assert point.vector == vector
        assert point.payload == payload


def test_upsert_points_ignores_empty_or_mismatched_batches(
    store_and_client: tuple[qdrant.QdrantStore, FakeQdrantClient],
) -> None:
    store, client = store_and_client

    store.upsert_points([], [])
    store.upsert_points([[0.1]], [{"university_slug": "stanford"}, {"university_slug": "mit"}])

    assert client.upserted == []
