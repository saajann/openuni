from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
import yaml
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from app.core import universities
from app.core.config import get_settings
from app.rag import retrieval


@pytest.fixture
def temp_universities_dir(tmp_path: Path) -> Iterator[None]:
    settings = get_settings()
    original_dir = settings.universities_dir
    settings.universities_dir = tmp_path

    demo_dir = tmp_path / "demo"
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
    universities.load_universities()

    yield

    settings.universities_dir = original_dir
    universities.load_universities()


def test_retrieve_chunks_returns_ranked_matches(
    temp_universities_dir: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(retrieval, "_embed_question", lambda **_: [0.1, 0.2, 0.3])

    clients = []

    class FakeQdrantClient:
        def __init__(self, *, url: str):
            self.url = url
            self.closed = False
            clients.append(self)

        def close(self) -> None:
            self.closed = True

        def query_points(
            self,
            *,
            collection_name: str,
            query: list[float],
            limit: int,
            with_payload: bool,
        ) -> SimpleNamespace:
            assert collection_name == "demo_collection"
            assert query == [0.1, 0.2, 0.3]
            assert limit == 2
            assert with_payload is True
            return SimpleNamespace(
                points=[
                    SimpleNamespace(
                        payload={
                            "chunk_text": "Deadlines are in September.",
                            "source": "handbook.pdf",
                        },
                        score=0.91,
                    ),
                    SimpleNamespace(
                        payload={
                            "chunk_text": "Tuition info.",
                            "source_url_or_filename": "fees.md",
                        },
                        score=0.74,
                    ),
                ]
            )

    monkeypatch.setattr(retrieval, "QdrantClient", FakeQdrantClient)

    chunks = retrieval.retrieve_chunks("demo", "When are deadlines?", top_k=2)

    assert len(chunks) == 2
    assert chunks[0].chunk_text == "Deadlines are in September."
    assert chunks[0].source == "handbook.pdf"
    assert chunks[0].score == 0.91
    assert chunks[1].source == "fees.md"
    assert len(clients) == 1 and clients[0].closed


def test_retrieve_chunks_returns_empty_for_missing_collection(
    temp_universities_dir: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(retrieval, "_embed_question", lambda **_: [0.1, 0.2, 0.3])

    clients = []

    class FakeQdrantClient:
        def __init__(self, *, url: str):
            self.url = url
            self.closed = False
            clients.append(self)

        def close(self) -> None:
            self.closed = True

        def query_points(
            self,
            *,
            collection_name: str,
            query: list[float],
            limit: int,
            with_payload: bool,
        ) -> SimpleNamespace:
            raise UnexpectedResponse(
                status_code=404,
                reason_phrase="Not Found",
                content=b"",
                headers=httpx.Headers({}),
            )

    monkeypatch.setattr(retrieval, "QdrantClient", FakeQdrantClient)

    chunks = retrieval.retrieve_chunks("demo", "Any scholarships?")

    assert chunks == []
    assert len(clients) == 1 and clients[0].closed


def test_retrieve_chunks_closes_client_on_query_error(
    temp_universities_dir: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(retrieval, "_embed_question", lambda **_: [0.1, 0.2, 0.3])
    clients = []

    class FakeQdrantClient:
        def __init__(self, *, url: str):
            self.closed = False
            clients.append(self)

        def query_points(self, **kwargs: object) -> None:
            raise RuntimeError("query failed")

        def close(self) -> None:
            self.closed = True

    monkeypatch.setattr(retrieval, "QdrantClient", FakeQdrantClient)
    with pytest.raises(RuntimeError, match="query failed"):
        retrieval.retrieve_chunks("demo", "Any scholarships?")
    assert len(clients) == 1 and clients[0].closed


def test_embedding_failure_raises_retrieval_unavailable(
    temp_universities_dir: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "post", fail)

    with pytest.raises(retrieval.RetrievalUnavailable):
        retrieval.retrieve_chunks("demo", "When are deadlines?")


def test_qdrant_server_error_raises_retrieval_unavailable(
    temp_universities_dir: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(retrieval, "_embed_question", lambda **_: [0.1, 0.2, 0.3])
    clients = []

    class FakeQdrantClient:
        def __init__(self, *, url: str):
            self.closed = False
            clients.append(self)

        def query_points(
            self,
            *,
            collection_name: str,
            query: list[float],
            limit: int,
            with_payload: bool,
        ) -> SimpleNamespace:
            raise UnexpectedResponse(
                status_code=503,
                reason_phrase="Service Unavailable",
                content=b"",
                headers=httpx.Headers({}),
            )

        def close(self) -> None:
            self.closed = True

    monkeypatch.setattr(retrieval, "QdrantClient", FakeQdrantClient)

    with pytest.raises(retrieval.RetrievalUnavailable):
        retrieval.retrieve_chunks("demo", "Any scholarships?")
    assert len(clients) == 1 and clients[0].closed


def test_qdrant_connection_error_raises_retrieval_unavailable(
    temp_universities_dir: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(retrieval, "_embed_question", lambda **_: [0.1, 0.2, 0.3])
    clients = []

    class FakeQdrantClient:
        def __init__(self, *, url: str):
            self.closed = False
            clients.append(self)

        def query_points(self, **kwargs: object) -> None:
            raise ResponseHandlingException(httpx.ConnectError("connection refused"))

        def close(self) -> None:
            self.closed = True

    monkeypatch.setattr(retrieval, "QdrantClient", FakeQdrantClient)

    with pytest.raises(retrieval.RetrievalUnavailable):
        retrieval.retrieve_chunks("demo", "Any scholarships?")
    assert len(clients) == 1 and clients[0].closed
