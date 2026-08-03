import pytest

from ingestion.embeddings import ollama


class FakeResponse:
    def __init__(self, data: dict) -> None:
        self.data = data

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.data


def test_ensure_model_pulled_skips_pull_when_model_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"get": 0, "post": 0}

    def fake_get(url: str) -> FakeResponse:
        assert url == "http://localhost:11434/api/tags"
        calls["get"] += 1
        return FakeResponse({"models": [{"name": "nomic-embed-text:latest"}]})

    def fake_post(*args, **kwargs) -> None:
        calls["post"] += 1
        raise AssertionError("post should not be called when the model already exists")

    monkeypatch.setattr(ollama.httpx, "get", fake_get)
    monkeypatch.setattr(ollama.httpx, "post", fake_post)

    ollama.OllamaEmbedder().ensure_model_pulled()

    assert calls == {"get": 1, "post": 0}


def test_ensure_model_pulled_pulls_missing_model(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str) -> FakeResponse:
        assert url == "http://localhost:11434/api/tags"
        return FakeResponse({"models": []})

    post_calls: list[tuple[str, dict]] = []

    def fake_post(url: str, **kwargs) -> FakeResponse:
        post_calls.append((url, kwargs))
        return FakeResponse({"status": "success"})

    monkeypatch.setattr(ollama.httpx, "get", fake_get)
    monkeypatch.setattr(ollama.httpx, "post", fake_post)

    ollama.OllamaEmbedder().ensure_model_pulled()

    assert len(post_calls) == 1
    url, kwargs = post_calls[0]
    assert url == "http://localhost:11434/api/pull"
    assert kwargs == {
        "json": {"name": "nomic-embed-text", "stream": False},
        "timeout": 300.0,
    }


def test_embed_documents_returns_embeddings(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        instances: list["FakeClient"] = []

        def __init__(self, **kwargs) -> None:
            self.timeout = kwargs["timeout"]
            self.posts: list[tuple[str, dict]] = []
            self.instances.append(self)

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *args) -> None:
            return None

        def post(self, url: str, **kwargs) -> FakeResponse:
            self.posts.append((url, kwargs))
            return FakeResponse({"embedding": [0.1, 0.2, 0.3]})

    monkeypatch.setattr(ollama.httpx, "Client", FakeClient)

    embeddings = ollama.OllamaEmbedder().embed_documents(["hello", "world"])

    assert embeddings == [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]
    client = FakeClient.instances[0]
    assert client.timeout == 60.0
    assert [url for url, _ in client.posts] == [
        "http://localhost:11434/api/embeddings",
        "http://localhost:11434/api/embeddings",
    ]
    assert all(kwargs["json"]["model"] == "nomic-embed-text" for _, kwargs in client.posts)
