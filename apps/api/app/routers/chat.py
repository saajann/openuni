"""
apps/api/app/routers/chat.py
────────────────────────────
POST /chat — the main RAG endpoint.

Validates the incoming request, delegates to the retrieval and generation
layers, and returns a structured answer with cited sources.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.core.universities import get_university
from app.models.chat import ChatRequest, ChatResponse, SourceItem
from app.rag.generation import generate_answer
from app.rag.retrieval import retrieve_chunks

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
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"University '{body.university_slug}' not found.",
        )

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
    chunks = retrieve_chunks(university_slug=body.university_slug, question=body.question)

    # ── Generation ────────────────────────────────────────────────────────────
    generated = generate_answer(question=body.question, chunks=chunks)

    return ChatResponse(
        answer=generated.answer,
        sources=[
            SourceItem(text_snippet=s.text_snippet, source=s.source)
            for s in generated.sources
        ],
    )
