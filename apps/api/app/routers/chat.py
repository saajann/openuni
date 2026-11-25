"""
apps/api/app/routers/chat.py
────────────────────────────
POST /chat — the main RAG endpoint.

Validates the incoming request, delegates to the retrieval and generation
layers, and returns a structured answer with cited sources.

Retrieval and generation currently use synchronous network clients (``httpx``,
``QdrantClient`` and the OpenAI SDK).  Both calls are therefore executed in a
worker thread via Starlette's ``run_in_threadpool`` so a slow embedding, vector
search or LLM request cannot block the event loop (and with it ``/health`` or
other in-flight requests).  Keeping the synchronous helpers unchanged also
keeps them straightforward to unit test.
"""

import logging

from fastapi import APIRouter, HTTPException, status
from starlette.concurrency import run_in_threadpool

from app.core.universities import get_university
from app.models.chat import ChatRequest, ChatResponse, SourceItem
from app.rag.generation import LLMProviderUnavailable, generate_answer
from app.rag.retrieval import RetrievalUnavailable, retrieve_chunks

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


@router.post(
    "/chat",
    summary="Ask a question about a university",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
async def chat(body: ChatRequest) -> ChatResponse:
    """RAG-powered question answering for a specific university.

    1. Validates ``university_slug`` against the loaded registry — **404** if unknown.
    2. Validates ``question`` is non-empty — **422** is handled automatically by
       Pydantic; an explicit guard covers whitespace-only strings.
    3. Calls ``retrieve_chunks`` then ``generate_answer`` and maps the result to
       the public response schema.
    """
    # ── Validate university ───────────────────────────────────────────────────
    try:
        get_university(body.university_slug)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"University '{body.university_slug}' not found.",
        ) from e

    # ── Validate question ─────────────────────────────────────────────────────
    if not body.question.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="question must not be empty or whitespace.",
        )

    # ── Basic request logging (no answer logged) ──────────────────────────────
    logger.info(
        "chat request university=%s question=%r",
        body.university_slug,
        body.question[:120],
    )

    # ── Retrieval ─────────────────────────────────────────────────────────────
    # Offload the blocking HTTP/vector-store calls so the event loop stays free.
    try:
        chunks = await run_in_threadpool(
            retrieve_chunks,
            university_slug=body.university_slug,
            question=body.question,
        )
    except RetrievalUnavailable as exc:
        logger.warning("chat retrieval unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Retrieval is temporarily unavailable. Please try again shortly.",
        ) from exc

    # ── Generation ────────────────────────────────────────────────────────────
    try:
        generated = await run_in_threadpool(
            generate_answer,
            question=body.question,
            chunks=chunks,
        )
    except LLMProviderUnavailable as exc:
        logger.warning("chat generation unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Answer generation is temporarily unavailable. Please try again shortly.",
        ) from exc

    return ChatResponse(
        answer=generated.answer,
        sources=[
            SourceItem(text_snippet=s.text_snippet, source=s.source) for s in generated.sources
        ],
    )
