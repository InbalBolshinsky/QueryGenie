"""The QueryGenie agent: an LLM with SQL tools, driven by a plain tool-calling loop.

The model decides what to investigate, runs queries, reads the results (or errors),
fixes its own SQL, and saves the insights worth charting. Every step is yielded as an
event so the UI can show the agent working in real time.
"""

import json
from collections.abc import Iterator

from openai import OpenAI
from pydantic import BaseModel

from .db import Database, QueryError

MAX_STEPS = 25
MIN_INSIGHTS = 3
ROWS_SHOWN_TO_MODEL = 20
ROWS_PER_CHART = 50


class Profile(BaseModel):
    company_name: str
    company_description: str
    job_title: str
    job_responsibilities: str


SYSTEM_PROMPT = """You are QueryGenie, a senior data analyst. A business user describes their company and role; \
you find the insights from their SQLite database that matter most for that role.

How to work:
1. Explore with run_sql. Check the date range of the data (e.g. MIN/MAX of order dates) before any time-based \
query; the data is historical, so never use the current date.
2. When a query answers a question that matters for this role, call save_insight. Aim for 5 varied insights \
(trends over time, rankings, breakdowns, key numbers) and use the chart type that fits the data.
3. If a query fails, read the error and fix it. Do not save an insight whose query you have not run.
4. Call finish with 3-5 concise, specific findings for this person (use real numbers).

Before each tool call, write one short sentence saying what you are about to check and why.

SQLite notes: quote table names containing spaces, e.g. "Order Details". Use strftime('%Y', date) for years. \
Give result columns readable aliases.

Database schema:
{schema}"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": f"Run a read-only SQLite SELECT query. Returns up to {ROWS_SHOWN_TO_MODEL} rows, or an error.",
            "parameters": {
                "type": "object",
                "properties": {"sql": {"type": "string"}},
                "required": ["sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_insight",
            "description": (
                "Save an insight to show the user as a chart. The query is re-run to get the data. "
                "bar/line/pie need label_column and value_column; number needs value_column (single row); "
                "table shows the rows as-is."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The business question, in plain language."},
                    "sql": {"type": "string"},
                    "chart": {"type": "string", "enum": ["bar", "line", "pie", "number", "table"]},
                    "label_column": {"type": "string", "description": "Column for the x-axis / slice labels."},
                    "value_column": {"type": "string", "description": "Numeric column to plot."},
                    "takeaway": {"type": "string", "description": "One sentence: what the data shows."},
                },
                "required": ["question", "sql", "chart", "takeaway"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "End the analysis with the overall summary for the user.",
            "parameters": {
                "type": "object",
                "properties": {"summary": {"type": "array", "items": {"type": "string"}}},
                "required": ["summary"],
            },
        },
    },
]


def run_agent(profile: Profile, db: Database, client: OpenAI, model: str) -> Iterator[dict]:
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT.format(schema=db.schema())},
        {"role": "user", "content": "\n".join(f"{k.replace('_', ' ').title()}: {v}" for k, v in profile)},
    ]
    insights: list[dict] = []

    for _ in range(MAX_STEPS):
        response = client.chat.completions.create(model=model, messages=messages, tools=TOOLS)
        message = response.choices[0].message
        # model_dump keeps provider-specific fields (e.g. Gemini thought signatures) intact.
        messages.append(message.model_dump(exclude_none=True))

        if message.content and message.content.strip():
            yield {"type": "thought", "text": message.content.strip()}

        if not message.tool_calls:
            messages.append({"role": "user", "content": "Continue using the tools, and call finish when you are done."})
            continue

        summary = None
        for call in message.tool_calls:
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = None

            if args is None:
                result = {"error": "Tool arguments were not valid JSON."}
            elif call.function.name == "run_sql":
                result = yield from _run_sql(db, args.get("sql", ""))
            elif call.function.name == "save_insight":
                result = yield from _save_insight(db, args, insights)
            elif call.function.name == "finish":
                if len(insights) < MIN_INSIGHTS:
                    result = {"error": f"Save at least {MIN_INSIGHTS} insights before finishing (you have {len(insights)})."}
                else:
                    summary = [str(s) for s in args.get("summary", [])]
                    result = {"ok": True}
            else:
                result = {"error": f"Unknown tool {call.function.name}."}

            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, default=str)})

        if summary is not None:
            yield {"type": "done", "summary": summary}
            return

    if insights:
        yield {"type": "done", "summary": ["The agent reached its step limit; the insights above are what it found."]}
    else:
        yield {"type": "error", "message": "The agent could not produce any insights. Please try again."}


def _run_sql(db: Database, sql: str) -> Iterator[dict]:
    try:
        columns, rows, truncated = db.query(sql, max_rows=ROWS_SHOWN_TO_MODEL)
    except QueryError as e:
        yield {"type": "query", "sql": sql, "ok": False, "error": str(e)}
        return {"error": str(e)}
    yield {"type": "query", "sql": sql, "ok": True, "rows": len(rows)}
    return {"columns": columns, "rows": rows, "truncated": truncated}


def _save_insight(db: Database, args: dict, insights: list[dict]) -> Iterator[dict]:
    chart = args.get("chart")
    label, value = args.get("label_column"), args.get("value_column")
    try:
        columns, rows, _ = db.query(args.get("sql", ""), max_rows=ROWS_PER_CHART)
    except QueryError as e:
        return {"error": f"Query failed: {e}"}

    needed = {"bar": [label, value], "line": [label, value], "pie": [label, value], "number": [value]}.get(chart, [])
    missing = [c for c in needed if c not in columns]
    if missing or not rows:
        problem = "The query returned no rows." if not rows else f"Columns {missing} not in result {columns}."
        return {"error": f"Insight not saved. {problem}"}

    insight = {
        "question": args.get("question", ""),
        "takeaway": args.get("takeaway", ""),
        "sql": args["sql"],
        "chart": chart,
        "label_column": label,
        "value_column": value,
        "columns": columns,
        "rows": rows,
    }
    insights.append(insight)
    yield {"type": "insight", "insight": insight}
    return {"ok": True, "saved_insights": len(insights)}
