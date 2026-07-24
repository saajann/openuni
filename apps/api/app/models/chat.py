"""
apps/api/app/models/chat.py
───────────────────────────
Pydantic schemas for the POST /chat endpoint.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    university_slug: str = Field(..., description="Slug of the target university.")
    question: str = Field(..., description="Natural-language question from the user.")


class SourceItem(BaseModel):
    """A single cited source returned alongside the answer."""

    text_snippet: str = Field(..., description="Short verbatim excerpt (≤ 120 chars).")
    source: str = Field(..., description="Source identifier (filename, URL, etc.).")


class ChatResponse(BaseModel):
    """Response body for the chat endpoint."""

    answer: str = Field(..., description="Grounded answer with inline citations.")
    sources: list[SourceItem] = Field(
        default_factory=list,
        description="Cited passages that support the answer.",
    )
