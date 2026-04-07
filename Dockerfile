FROM python:3.11-slim AS builder
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl && \
    rm -rf /var/lib/apt/lists/*

ARG BUILD_MODE=in-repo
ARG ENV_NAME=openenv_invotex

COPY . /app/env
WORKDIR /app/env

# Install uv if not already present
RUN if ! command -v uv >/dev/null 2>&1; then \
        curl -LsSf https://astral.sh/uv/install.sh | sh && \
        mv /root/.local/bin/uv /usr/local/bin/uv && \
        mv /root/.local/bin/uvx /usr/local/bin/uvx; \
    fi

# Install dependencies only (no project install yet)
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -f uv.lock ]; then \
        uv sync --frozen --no-install-project --no-editable; \
    else \
        uv sync --no-install-project --no-editable; \
    fi

# Install project
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -f uv.lock ]; then \
        uv sync --frozen --no-editable; \
    else \
        uv sync --no-editable; \
    fi

# ─── Runtime stage ────────────────────────────────────────────────────────────
FROM python:3.11-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# HuggingFace Spaces requires UID 1000
RUN useradd -m -u 1000 user
RUN mkdir -p /app && chown -R user:user /app

USER user

ENV PATH=/app/.venv/bin:$PATH \
    PYTHONPATH=/app/env \
    ENABLE_WEB_INTERFACE=true \
    DATABASE_URL=sqlite:////tmp/env.db \
    DOMAIN=email_triage

WORKDIR /app

COPY --from=builder --chown=user:user /app/env/.venv /app/.venv
COPY --from=builder --chown=user:user /app/env /app/env

HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=5 \
    CMD curl -f http://localhost:7860/health || exit 1

CMD ["sh", "-c", "cd /app/env && uvicorn server.app:app --host 0.0.0.0 --port 7860 --workers 1"]
