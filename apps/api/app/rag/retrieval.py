from dataclasses import dataclass
from typing import Any

import httpx
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import get_settings
from app.core.universities import get_university


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_text: str
    source: str | None
    score: float


def _embed_question(question: str, ollama_url: str, model: str) -> list[float]:
    response = httpx.post(
        f"{ollama_url.rstrip('/')}/api/embeddings",
        json={"model": model, "prompt": question},
        timeout=30.0,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("Embedding response was not a JSON object.")

    embedding = data.get("embedding")
    if (
        not isinstance(embedding, list)
        or not embedding
        or not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in embedding)
    ):
        raise ValueError("Embedding response did not contain a numeric 'embedding' vector.")

    return [float(x) for x in embedding]


def _source_from_payload(payload: dict[str, Any]) -> str | None:
    source = payload.get("source") or payload.get("source_url_or_filename")
    return source if isinstance(source, str) else None


def retrieve_chunks(university_slug: str, question: str, top_k: int = 5) -> list[RetrievedChunk]:
    if not question.strip() or top_k <= 0:
        return []

    settings = get_settings()
    university = get_university(university_slug)
    embedding = _embed_question(
        question=question,
        ollama_url=str(settings.ollama_url),
        model=settings.embedding_model,
    )
    qdrant = QdrantClient(url=str(settings.qdrant_url))
    try:
        # qdrant-client's type stubs don't declare `search` on this overload
        # of QdrantClient even though it exists and works at runtime.
        points = qdrant.search(  # type: ignore[attr-defined]
            collection_name=university.qdrant_collection,
            query_vector=embedding,
            limit=top_k,
            with_payload=True,
        )
    except UnexpectedResponse as exc:
        if exc.status_code == 404:
            return []
        raise

    chunks: list[RetrievedChunk] = []
    for point in points:
        payload = point.payload if isinstance(point.payload, dict) else {}
        chunk_text = payload.get("chunk_text")
        if not isinstance(chunk_text, str) or not chunk_text:
            continue
        chunks.append(
            RetrievedChunk(
                chunk_text=chunk_text,
                source=_source_from_payload(payload),
                score=float(point.score),
            )
        )
    return chunks
