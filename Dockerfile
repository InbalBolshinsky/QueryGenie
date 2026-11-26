# One image serves both the API and the built React app.

FROM node:24-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
RUN pip install --no-cache-dir uv
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend/app ./app
COPY --from=frontend /app/frontend/dist /app/frontend/dist
# Bake the demo database into the image so cold starts don't re-download it.
RUN uv run --no-sync python -c "from pathlib import Path; from app.db import ensure_northwind; ensure_northwind(Path('data/northwind.db'))"

ENV PATH="/app/backend/.venv/bin:$PATH"
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
