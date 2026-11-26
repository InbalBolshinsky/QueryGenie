"""Tests run the real agent loop and API against a tiny SQLite DB, with a scripted fake LLM."""

import json
import sqlite3

import httpx
import openai
import pytest
from fastapi.testclient import TestClient
from openai.types.chat import ChatCompletion

from app import main
from app.agent import Profile, run_agent
from app.db import Database, QueryError

PROFILE = Profile(
    company_name="Acme Foods",
    company_description="Food distributor",
    job_title="Sales Manager",
    job_responsibilities="Grow revenue",
)


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "test.db"
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE "Order Details" (Product TEXT, Revenue REAL)')
        conn.executemany('INSERT INTO "Order Details" VALUES (?, ?)', [("Tea", 120.0), ("Cheese", 80.5), ("Bread", 40.0)])
    return Database(path)


def tool_call(name: str, **args) -> dict:
    return {"name": name, "args": args}


class FakeLLM:
    """Mimics openai.OpenAI: each create() returns the next scripted turn and records what it was sent."""

    def __init__(self, turns: list[list[dict]]):
        self.turns = iter(turns)
        self.requests: list[list[dict]] = []
        self.chat = self
        self.completions = self

    def create(self, model, messages, **_):
        self.requests.append(list(messages))
        calls = next(self.turns)
        return ChatCompletion.model_validate({
            "id": "x", "object": "chat.completion", "created": 0, "model": model,
            "choices": [{
                "index": 0, "finish_reason": "tool_calls",
                "message": {
                    "role": "assistant",
                    "content": "Checking something.",
                    "tool_calls": [
                        {"id": f"call_{i}", "type": "function",
                         "function": {"name": c["name"], "arguments": json.dumps(c["args"])}}
                        for i, c in enumerate(calls)
                    ],
                },
            }],
        })


INSIGHT = dict(
    question="Which products earn the most?",
    sql='SELECT Product, Revenue FROM "Order Details" ORDER BY Revenue DESC',
    chart="bar", label_column="Product", value_column="Revenue", takeaway="Tea leads.",
)

HAPPY_PATH = [
    [tool_call("run_sql", sql="SELECT * FROM Order Details")],  # broken SQL: unquoted name
    [tool_call("run_sql", sql=INSIGHT["sql"])],                  # self-corrected
    [tool_call("save_insight", **INSIGHT)] * 3,                  # parallel tool calls
    [tool_call("finish", summary=["Tea is the top product."])],
]


def test_agent_recovers_from_sql_error_and_finishes(db):
    llm = FakeLLM(HAPPY_PATH)
    events = list(run_agent(PROFILE, db, llm, ["fake-model"]))
    types = [e["type"] for e in events]

    queries = [e for e in events if e["type"] == "query"]
    assert queries[0]["ok"] is False and "syntax error" in queries[0]["error"]
    assert queries[1]["ok"] is True and queries[1]["rows"] == 3

    # The SQL error was fed back to the model so it could fix the query.
    tool_msgs = [m for m in llm.requests[1] if m["role"] == "tool"]
    assert "syntax error" in tool_msgs[0]["content"]

    insights = [e["insight"] for e in events if e["type"] == "insight"]
    assert len(insights) == 3
    assert insights[0]["rows"][0] == {"Product": "Tea", "Revenue": 120.0}

    assert types[-1] == "done" and events[-1]["summary"] == ["Tea is the top product."]
    assert "thought" in types


def test_finish_is_rejected_until_enough_insights(db):
    llm = FakeLLM([
        [tool_call("finish", summary=["too early"])],
        [tool_call("save_insight", **INSIGHT)] * 3,
        [tool_call("finish", summary=["done"])],
    ])
    events = list(run_agent(PROFILE, db, llm, ["fake-model"]))
    first_result = [m for m in llm.requests[1] if m["role"] == "tool"][0]
    assert "at least 3 insights" in first_result["content"]
    assert events[-1] == {"type": "done", "summary": ["done"]}


def test_invalid_chart_columns_are_reported_to_model(db):
    llm = FakeLLM([
        [tool_call("save_insight", **{**INSIGHT, "value_column": "Profit"})],
        [tool_call("save_insight", **INSIGHT)] * 3,
        [tool_call("finish", summary=["ok"])],
    ])
    events = list(run_agent(PROFILE, db, llm, ["fake-model"]))
    first_result = [m for m in llm.requests[1] if m["role"] == "tool"][0]
    assert "not in result" in first_result["content"]
    assert sum(e["type"] == "insight" for e in events) == 3


def test_falls_back_to_next_model_when_busy(db):
    class BusyFirstModel(FakeLLM):
        def create(self, model, messages, **kwargs):
            if model == "busy-model":
                request = httpx.Request("POST", "https://llm.test")
                raise openai.InternalServerError("busy", response=httpx.Response(503, request=request), body=None)
            return super().create(model, messages, **kwargs)

    events = list(run_agent(PROFILE, db, BusyFirstModel(HAPPY_PATH), ["busy-model", "backup-model"]))
    assert "switching to backup-model" in events[0]["text"]
    assert events[-1]["type"] == "done"


def test_database_is_read_only(db):
    with pytest.raises(QueryError):
        db.query('DELETE FROM "Order Details"')
    with pytest.raises(QueryError, match="readonly"):
        db.query('WITH x AS (SELECT 1) DELETE FROM "Order Details"')
    assert len(db.query('SELECT * FROM "Order Details"')[1]) == 3


def test_query_truncates_rows(db):
    _, rows, truncated = db.query('SELECT * FROM "Order Details"', max_rows=2)
    assert len(rows) == 2 and truncated


def test_schema_quotes_table_names(db):
    assert '"Order Details"(Product TEXT, Revenue REAL)' in db.schema()


def test_analyze_endpoint_streams_ndjson(db, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(db.path))  # skips the Northwind download
    monkeypatch.setattr(main, "db", db)
    monkeypatch.setattr(main, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(main, "get_llm", lambda: FakeLLM(HAPPY_PATH))
    with TestClient(main.app) as client:
        response = client.post("/api/analyze", json=PROFILE.model_dump())
        assert response.headers["content-type"].startswith("application/x-ndjson")
        events = [json.loads(line) for line in response.text.splitlines()]
        assert events[-1]["type"] == "done"
        assert client.get("/api/health").json()["model"] == main.LLM_MODEL
