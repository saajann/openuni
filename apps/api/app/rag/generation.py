"""
apps/api/app/rag/generation.py
──────────────────────────────
Generation step of the RAG pipeline.

Given a question and a list of retrieved chunks, this module:
  1. Short-circuits with a fixed response when no context is available.
  2. Builds a structured prompt that instructs the model to answer *only*
     from the supplied context and to cite the source of each claim.
  3. Calls the OpenAI Chat Completions API and parses the response into a
     structured ``GeneratedAnswer``.

LLM provider (v0): **OpenAI** (``gpt-4o-mini`` by default).
Rationale: widely available, excellent instruction-following, JSON-mode
support makes structured output straightforward.  See README.md §LLM
Provider for the full decision record.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from openai import OpenAI

from app.core.config import get_settings
from app.rag.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

_NO_INFORMATION_ANSWER = (
    "I don't have information about this in the provided context. "
    "Please contact the university directly or check their official website."
)

_SYSTEM_PROMPT = """\
You are a helpful university information assistant.
Your job is to answer the user's question using ONLY the numbered context \
passages provided below.

Rules you MUST follow:
1. Base every statement exclusively on the provided passages.
2. Never invent, assume, or infer information that is not explicitly stated \
   in the context.
3. If the passages do not contain enough information to answer the question, \
   say so clearly — do not guess.
4. For every sentence or claim in your answer, cite the passage number(s) \
   that support it using the format [1], [2], etc.
5. Return a JSON object with exactly two keys:
   - "answer": a clear, concise answer string with inline citations.
   - "sources": a list of objects, each with:
       - "text_snippet": a short verbatim excerpt (≤ 120 chars) from the \
         passage that directly supports a claim in the answer.
       - "source": the source identifier of that passage.
   Only include passages that were actually cited in the answer.
6. Output raw JSON only — no markdown fences, no extra commentary.\
"""

_CONTEXT_BLOCK_TEMPLATE = "--- Passage [{index}] (source: {source}) ---\n{text}\n"


# ── Data models ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CitedSource:
    """A verbatim snippet and its origin, extracted from a cited chunk."""

    text_snippet: str
    source: str


@dataclass(frozen=True)
class GeneratedAnswer:
    """Structured output of the generation step."""

    answer: str
    sources: list[CitedSource] = field(default_factory=list)


# ── Internal helpers ──────────────────────────────────────────────────────────


def _build_user_message(question: str, chunks: list[RetrievedChunk]) -> str:
    """Assemble the user turn: context passages followed by the question."""
    passages = []
    for i, chunk in enumerate(chunks, start=1):
        source_label = chunk.source or "unknown"
        passages.append(
            _CONTEXT_BLOCK_TEMPLATE.format(
                index=i,
                source=source_label,
                text=chunk.chunk_text.strip(),
            )
        )
    context_block = "\n".join(passages)
    return f"{context_block}\n\nQuestion: {question}"


def _parse_llm_response(raw: str) -> GeneratedAnswer:
    """Parse the model's JSON output into a ``GeneratedAnswer``.

    Falls back to returning the raw text as the answer (with no sources)
    if the JSON is malformed, so callers always receive a usable result.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("LLM returned non-JSON output; returning raw text.")
        return GeneratedAnswer(answer=raw.strip(), sources=[])

    answer = data.get("answer", "").strip()
    raw_sources = data.get("sources", [])

    sources: list[CitedSource] = []
    for item in raw_sources:
        if not isinstance(item, dict):
            continue
        snippet = item.get("text_snippet", "")
        src = item.get("source", "unknown")
        if isinstance(snippet, str) and snippet:
            sources.append(CitedSource(text_snippet=snippet, source=str(src)))

    return GeneratedAnswer(answer=answer, sources=sources)


# ── Public API ────────────────────────────────────────────────────────────────


def generate_answer(
    question: str,
    chunks: list[RetrievedChunk],
    *,
    model: str | None = None,
    client: OpenAI | None = None,
) -> GeneratedAnswer:
    """Generate a grounded, cited answer from retrieved context chunks.

    Parameters
    ----------
    question:
        The user's natural-language question.
    chunks:
        Retrieved context chunks from the vector store.  When this list is
        empty the function returns a fixed "no information" response without
        making any LLM call.
    model:
        OpenAI model name to use.  Defaults to ``Settings.openai_model``.
    client:
        An ``openai.OpenAI`` client instance.  Injected here primarily to
        allow deterministic unit testing without network calls; if omitted
        a default client is created from the application settings.

    Returns
    -------
    GeneratedAnswer
        Structured answer with inline citations and a list of cited sources.
    """
    if not chunks:
        return GeneratedAnswer(answer=_NO_INFORMATION_ANSWER, sources=[])

    settings = get_settings()
    resolved_model = model or settings.openai_model
    resolved_client = client or OpenAI(api_key=settings.openai_api_key.get_secret_value())

    user_message = _build_user_message(question, chunks)

    logger.debug(
        "Calling OpenAI model=%s with %d context chunk(s).",
        resolved_model,
        len(chunks),
    )

    response = resolved_client.chat.completions.create(
        model=resolved_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,  # deterministic; citations must be grounded
    )

    raw_content: str = response.choices[0].message.content or ""
    return _parse_llm_response(raw_content)
