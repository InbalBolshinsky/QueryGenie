import json
import logging
import os
from collections.abc import Iterator
from contextlib import asynccontextmanager
from pathlib import Path

import openai
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from .agent import Profile, run_agent
from .db import Database, ensure_northwind

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

DB_PATH = Path(os.getenv("DATABASE_PATH", BACKEND_DIR / "data" / "northwind.db"))
FRONTEND_DIST = BACKEND_DIR.parent / "frontend" / "dist"

# Any OpenAI-compatible endpoint works. Default: Google Gemini's free tier.
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.8-flash")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
# Optional comma-separated backups, used when the main model is overloaded.
LLM_FALLBACK_MODELS = [m.strip() for m in os.getenv("LLM_FALLBACK_MODELS", "").split(",") if m.strip()]

db = Database(DB_PATH)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if "DATABASE_PATH" not in os.environ:
        ensure_northwind(DB_PATH)
    yield


app = FastAPI(title="QueryGenie", lifespan=lifespan)


def get_llm() -> openai.OpenAI:
    # The SDK retries 429/5xx/timeouts with backoff before the agent falls back to another model.
    return openai.OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY or "not-set", max_retries=2, timeout=60)


@app.get("/api/health")
def health():
    return {"database": DB_PATH.name, "model": LLM_MODEL, "llm_key_set": bool(LLM_API_KEY)}


@app.get("/api/schema")
def schema():
    return {"schema": db.schema()}


@app.post("/api/analyze")
def analyze(profile: Profile):
    return StreamingResponse(_ndjson(profile), media_type="application/x-ndjson")


def _ndjson(profile: Profile) -> Iterator[str]:
    if not LLM_API_KEY and "localhost" not in LLM_BASE_URL:
        yield _error("No LLM key configured. Add a free Gemini key as LLM_API_KEY in backend/.env (see .env.example).")
        return
    try:
        for event in run_agent(profile, db, get_llm(), [LLM_MODEL, *LLM_FALLBACK_MODELS]):
            yield json.dumps(event, default=str) + "\n"
    except openai.AuthenticationError:
        yield _error("The LLM rejected the API key. Set LLM_API_KEY in backend/.env.")
    except (openai.RateLimitError, openai.InternalServerError, openai.APITimeoutError):
        yield _error("The LLM is overloaded or rate-limited right now (free tier). Try again in a minute.")
    except openai.APIError as e:
        logging.exception("LLM error")
        yield _error(f"LLM error: {e}")


def _error(message: str) -> str:
    return json.dumps({"type": "error", "message": message}) + "\n"


# Serve the built React app (npm run build). Mounted last so it never shadows /api routes.
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
