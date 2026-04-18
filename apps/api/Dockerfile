# =============================================================================
# macro-invest-agent-platform — API image
# Build context: project root
# =============================================================================

FROM python:3.12-slim AS base

WORKDIR /app

# ---------------------------------------------------------------------------
# System dependencies
# ---------------------------------------------------------------------------
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Install Python dependencies before copying source for layer caching
# ---------------------------------------------------------------------------
COPY pyproject.toml README.md ./

# Create minimal package stubs so hatchling can resolve build targets
RUN mkdir -p agent apps core domain evals mcp pipelines \
    && touch agent/__init__.py apps/__init__.py core/__init__.py \
           domain/__init__.py evals/__init__.py mcp/__init__.py pipelines/__init__.py

RUN pip install --no-cache-dir .

# ---------------------------------------------------------------------------
# Copy application source
# ---------------------------------------------------------------------------
COPY apps/ apps/
COPY core/ core/
COPY agent/ agent/
COPY domain/ domain/
COPY adapters/ adapters/
COPY services/ services/
COPY pipelines/ pipelines/
COPY mcp/ mcp/

# ---------------------------------------------------------------------------
# Runtime configuration
# ---------------------------------------------------------------------------
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
