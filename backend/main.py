from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

import os
import re
import json
import logging
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, MetaData, text
from openai import OpenAI
from fasthtml.common import fast_app
from fastapi.responses import FileResponse
from starlette.routing import Mount

#print("🔐 Loaded API key:", os.getenv("OPENAI_API_KEY")[:10] + "...")

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI()

def rt(path: str, methods=["GET"]):
    def decorator(func):
        app.api_route(path, methods=methods)(func)
        return func
    return decorator

# Mount static files (JS, CSS, etc.)
static_path = Path(__file__).parent.parent / "frontend" / "static"
app.router.routes.append(
    Mount("/static", app=StaticFiles(directory=static_path), name="static")
)

# Favicon
@app.get("/GenieLamp.ico")
async def favicon():
    return FileResponse(static_path / "GenieLamp.ico")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve index.html
@rt("/")
def index():
    index_path = Path(__file__).parent.parent / "frontend" / "index.html"
    with open(index_path, "r", encoding="utf-8") as f:
        return Response(content=f.read(), media_type="text/html")

# Serve visualizations.html
@rt("/visualizations.html")
def visualizations():
    viz_path = Path(__file__).parent.parent / "frontend" / "visualizations.html"
    with open(viz_path, "r", encoding="utf-8") as f:
        return Response(content=f.read(), media_type="text/html")


# OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Database
DB_CONN = os.getenv("DATABASE_URL")
engine = create_engine(DB_CONN)

# Request model
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

            single_prompt = (
                f"You are a senior data analyst and MySQL expert.\n\n"
                f"Company Name: {data.company_name}\n"
                f"Company Description: {data.company_description}\n"
                f"Job Title: {data.job_title}\n"
                f"Job Responsibilities: {data.job_responsibilities}\n\n"
                f"Here is the database schema:\n{schema_str}\n\n"
                "Important context: The current date is **December 31, 2006**.\n"
                "All your analyses and time-based SQL filters should assume that today is 2006-12-31.\n"
                "Avoid using NOW(), CURDATE(), or 'last 3 months'. Instead, use concrete date ranges in 2006.\n\n"
                "Your task: Generate ONE relevant business question based on the job and data.\n"
                "Respond with ONLY a valid JSON object in this exact structure:\n"
                "{\n"
                "  \"question\": \"...\",\n"
                "  \"sql\": \"...\",\n"
                "  \"visualization\": \"Bar Chart | Line Chart | Pie Chart | etc.\"\n"
                "}\n"
                "Do not include any explanation, extra text, or markdown. Only valid JSON as shown above."
            )

            
            raw = ask_openai(single_prompt)
            logging.info(f"🔎 Raw GPT Response:\n{raw}")

            try:
                # Remove ```json ... ``` wrappers if GPT adds them
                cleaned_raw = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", raw.strip())
                parsed = json.loads(cleaned_raw)
                q = parsed["question"].strip()
                sql = ' '.join(parsed["sql"].split()).strip()
                viz = parsed["visualization"].strip()
            except Exception as e:
                logging.warning(f"❌ Failed to parse GPT response: {e}")
                logging.warning(f"⚠️ GPT raw response (cleaned):\n{cleaned_raw}")
                continue


            # Dedupe and skip if empty
            if not sql or q in seen_q or sql in seen_sql:
                continue

            # Execute & skip if fails or empty
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

        # Build summary
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

# --- Run server ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
