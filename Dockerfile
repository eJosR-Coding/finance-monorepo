# Prestameami.pe — one image, one service: FastAPI serves the API and the built SPA.
#
#   docker build -t prestameami .
#   docker run -p 8000:8000 -e PRESTAMEAMI_DATABASE_URL=postgresql://... prestameami

# ── 1. Frontend build ──────────────────────────────────────────────────────
FROM node:20-alpine AS web
WORKDIR /app/apps/web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

# ── 2. API runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv

# Business dates ("today", due dates, mora) follow Lima time, not the host's UTC.
RUN apt-get update \
 && apt-get install -y --no-install-recommends tzdata \
 && rm -rf /var/lib/apt/lists/*
ENV TZ=America/Lima \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app/apps/api
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY apps/api/ ./
COPY --from=web /app/apps/web/dist /app/apps/web/dist

ENV PATH="/app/apps/api/.venv/bin:$PATH"
EXPOSE 8000
# Render (and most hosts) pass the port in $PORT.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]
