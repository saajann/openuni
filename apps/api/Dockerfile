# apps/api/Dockerfile
# ─────────────────────────────────────────────────────────────────────────────
# Build:  docker build -t openuni-api .
# Run:    docker run --env-file ../../.env -p 8000:8000 openuni-api
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim AS base

# Keeps Python from buffering stdout/stderr and from generating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ── Dependencies layer (cached unless pyproject.toml changes) ─────────────────
COPY pyproject.toml ./

# Install the package in "no-build-isolation" editable mode so we get all
# dependencies declared in [project].  The trailing "." installs the local pkg.
RUN pip install --upgrade pip \
    && pip install .

# ── Application code ──────────────────────────────────────────────────────────
COPY app/ ./app/

# ── Non-root user for security ────────────────────────────────────────────────
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
