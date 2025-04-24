from dotenv import load_dotenv
from pathlib import Path
import os
import re
import json
import logging

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, MetaData, text
from openai import OpenAI
from starlette.routing import Mount
from fasthtml.common import fast_app

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI()


def rt(path: str, methods=["GET"]):
    def decorator(func):
        app.api_route(path, methods=methods)(func)
        return func
    return decorator


# Mount static files
build_path = Path(__file__).parent.parent / "querygenie-frontend" / "build"
# app.mount("/", StaticFiles(directory=build_path, html=True), name="frontend")


@app.get("/GenieLamp.ico")
async def favicon():
    return FileResponse(build_path / "GenieLamp.ico")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Database
DB_CONN = os.getenv("DATABASE_URL")
engine = create_engine(DB_CONN)


class AnalyzeRequest(BaseModel):
    company_name: str
    company_description: str
    job_title: str
    job_responsibilities: str


# --- Helper Functions ---
def get_db_schema():
    metadata = MetaData()
    metadata.reflect(engine)
    schema_str = ""
    for table in metadata.tables.values():
        schema_str += f"Table: {table.name}\n"
        for column in table.columns:
            schema_str += f"  - {column.name} ({column.type})\n"
    return schema_str


def ask_openai(prompt: str) -> str:
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"🔥 OpenAI error: {e}")
        import traceback
        traceback.print_exc()
        return ""


def execute_query(query: str):
    with engine.connect() as conn:
        try:
            result = conn.execute(text(query))
            return [dict(zip(result.keys(), row)) for row in result.fetchall()], result.keys()
        except Exception as e:
            logging.error(f"SQL execution error: {e}")
            return str(e), []


def get_summary(results_text: str) -> str:
    if "error" in results_text.lower():
        return "Some queries failed; unable to provide a reliable summary."
    summary_prompt = (
        f"Based on the following data analysis results:\n{results_text}\n"
        "What are the key insights or conclusions that can be derived?"
    )
    return ask_openai(summary_prompt)


def sanitize_json_string(raw: str) -> str:
    raw = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", raw.strip())

    def escape_string(match):
        content = match.group(1)
        content = content.replace('\n', '\\n').replace('\r', '')
        return f'"{content}"'

    return re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', escape_string, raw)


# --- API Endpoints ---
@rt("/schema")
def schema_preview():
    return {"schema": get_db_schema()}


@rt("/analyze", methods=["POST"])
def analyze(data: AnalyzeRequest):
    try:
        schema_str = get_db_schema()
        questions, queries, visualizations, results = [], [], [], []
        seen_q, seen_sql = set(), set()
        attempts, max_attempts = 0, 15

        while len(questions) < 5 and attempts < max_attempts:
            attempts += 1
            prompt = (
                f"You are a senior data analyst and MySQL expert.\n\n"
                f"Company Name: {data.company_name}\n"
                f"Company Description: {data.company_description}\n"
                f"Job Title: {data.job_title}\n"
                f"Job Responsibilities: {data.job_responsibilities}\n\n"
                f"Here is the database schema:\n{schema_str}\n\n"
                "Important context: The current date is **December 31, 2006**.\n"
                "All SQL queries must use fixed date ranges in 2006 (e.g., use '2006-01-01' to '2006-12-31').\n"
                "Avoid using dynamic expressions like NOW(), CURDATE(), or 'last 3 months'.\n\n"
                "Do not mention the year 2006 in the question. The user already knows this. Only use it in SQL filters.\n\n"
                "Your task: Generate ONE relevant business question based on the job and data.\n"
                "Respond with ONLY a valid JSON object in this exact structure:\n"
                "{\n"
                "  \"question\": \"...\",\n"
                "  \"sql\": \"...\",\n"
                "  \"visualization\": \"Bar Chart | Line Chart | Pie Chart | etc.\"\n"
                "}\n"
                "Do not include any explanation, extra text, or markdown. Only valid JSON as shown above."
            )

            raw = ask_openai(prompt)
            logging.info(f"🔎 Raw GPT Response:\n{raw}")

            try:
                cleaned_raw = sanitize_json_string(raw)
                parsed = json.loads(cleaned_raw)

                q = parsed["question"].strip()
                sql = ' '.join(parsed["sql"].split()).strip()
                viz = parsed["visualization"].strip()
            except Exception as e:
                logging.warning(f"❌ Failed to parse GPT response: {e}")
                logging.warning(f"⚠️ GPT raw response (cleaned):\n{cleaned_raw}")
                continue

            if not sql or q in seen_q or sql in seen_sql:
                continue

            res, _ = execute_query(sql)
            if isinstance(res, str) or not res:
                logging.info(f"❌ Skipped query: {sql}")
                continue

            questions.append(q)
            queries.append(sql)
            visualizations.append(viz)
            results.append(res)
            seen_q.add(q)
            seen_sql.add(sql)

        combined = "\n".join(f"Question: {q}\nResult: {r}" for q, r in zip(questions, results))
        summary = get_summary(combined)

        return {
            "company_name": data.company_name,
            "job_title": data.job_title,
            "company_description": data.company_description,
            "job_responsibilities": data.job_responsibilities,
            "schema": schema_str,
            "questions": questions,
            "queries": queries,
            "visualizations": visualizations,
            "results": results,
            "summary": summary
        }

    except Exception as e:
        logging.exception("Analyze error:")
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)