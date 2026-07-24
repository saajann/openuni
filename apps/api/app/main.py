"""
apps/api/app/main.py
────────────────────
FastAPI application entry-point.

Start locally (outside Docker):
    uvicorn app.main:app --reload --port 8000
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import psycopg
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core import universities
from app.core.config import Settings, get_settings
from app.routers import chat as chat_router


def _psycopg_dsn(sqlalchemy_url: str) -> str:
    """Convert a SQLAlchemy dialect URL to a bare psycopg3 DSN.

    SQLAlchemy uses ``postgresql+psycopg://…`` as its dialect specifier;
    psycopg3's ``AsyncConnection.connect`` only accepts ``postgresql://…``.
    """
    return sqlalchemy_url.replace("postgresql+psycopg", "postgresql", 1)


logger = logging.getLogger(__name__)


# ── Lifespan: startup / shutdown logic ────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: RUF029
    """Run connectivity probes on startup so bad config fails loudly."""
    settings: Settings = get_settings()

    # ── Probe Postgres ────────────────────────────────────────────────────────
    try:
        conn = await psycopg.AsyncConnection.connect(_psycopg_dsn(str(settings.database_url)))
        await conn.close()
        logger.info("✓ PostgreSQL reachable at %s", settings.database_url)
    except Exception as exc:
        logger.warning("✗ PostgreSQL not reachable: %s", exc)

    # ── Probe Qdrant ─────────────────────────────────────────────────────────
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.qdrant_url}/healthz")
            resp.raise_for_status()
        logger.info("✓ Qdrant reachable at %s", settings.qdrant_url)
    except Exception as exc:
        logger.warning("✗ Qdrant not reachable: %s", exc)

    # ── Load Universities ────────────────────────────────────────────────────
    universities.load_universities()

    yield  # application runs here

    logger.info("Shutting down OpenUni API")


# ── Application factory ────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="OpenUni API",
        description="AI-powered university assistant — RAG over official university documents.",
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # ── Global exception handler ──────────────────────────────────────────────
    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    application.include_router(chat_router.router)

    # ── Routes ────────────────────────────────────────────────────────────────
    class UniversityPublic(BaseModel):
        slug: str
        name: str
        locale: str
        domain: str

    @application.get(
        "/universities",
        summary="List available universities",
        tags=["universities"],
        response_model=list[UniversityPublic],
    )
    async def get_universities() -> list[UniversityPublic]:
        """Return the list of onboarded universities."""
        loaded = universities.list_universities()
        return [
            UniversityPublic(slug=u.slug, name=u.name, locale=u.locale, domain=u.domain)
            for u in loaded
        ]

    @application.get(
        "/health",
        summary="Health check",
        tags=["meta"],
        response_model=dict,
    )
    async def health() -> dict[str, str]:
        """Return a simple liveness signal.

        Used by Docker Compose health-checks, load balancers, and uptime
        monitors.  A 200 response means the process is running and the
        event loop is healthy — it does **not** guarantee that downstream
        dependencies (DB, vector store) are reachable.
        """
        return {"status": "ok"}

    @application.get(
        "/ready",
        summary="Readiness check",
        tags=["meta"],
        response_model=dict,
    )
    async def ready(request: Request) -> JSONResponse:
        """Probe downstream services and report their reachability.

        Returns HTTP 200 only when **all** dependencies respond.
        Returns HTTP 503 when any dependency is unavailable.
        """
        settings_obj: Settings = get_settings()
        checks: dict[str, str] = {}
        all_ok = True

        # Postgres
        try:
            dsn = _psycopg_dsn(str(settings_obj.database_url))
            conn = await psycopg.AsyncConnection.connect(dsn)
            await conn.close()
            checks["postgres"] = "ok"
        except Exception as exc:
            checks["postgres"] = f"error: {exc}"
            all_ok = False

        # Qdrant
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{settings_obj.qdrant_url}/healthz")
                resp.raise_for_status()
            checks["qdrant"] = "ok"
        except Exception as exc:
            checks["qdrant"] = f"error: {exc}"
            all_ok = False

        http_status = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        return JSONResponse(
            status_code=http_status,
            content={"status": "ready" if all_ok else "degraded", "checks": checks},
        )

    return application


app = create_app()
