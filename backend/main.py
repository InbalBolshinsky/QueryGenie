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
from sqlalchemy import create_engine, MetaData, text
from openai import OpenAI
from pydantic import BaseModel

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI()

# Mount React static build
build_path = Path(__file__).parent.parent / "querygenie-frontend" / "build"
if build_path.exists():
    app.mount("/", StaticFiles(directory=build_path, html=True), name="frontend")
else:
    logging.warning("⚠️ React build directory not found — skipping static mount.")


# Favicon endpoint
@app.get("/GenieLamp.ico")
async def favicon():
    return FileResponse(build_path / "GenieLamp.ico")

# CORS
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
        "Assume today is December 31, 2006.\n"
        "You are writing a final business summary report for a stakeholder.\n"
        "Write a structured and complete list of 5 bullet-point insights based only on the following results:\n\n"
        f"{results_text}\n\n"
        "Write clearly and do NOT repeat the year 2006. Do not trail off. Finish each bullet point with a full sentence."
    )
    return ask_openai(summary_prompt)

# --- API Endpoints ---
@app.get("/schema")
def schema_preview():
    return {"schema": get_db_schema()}

@app.post("/analyze")
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
                "Important context: The current date is December 31, 2006.\n"
                "All SQL queries must use fixed date ranges in 2006 (e.g., use '2006-01-01' to '2006-12-31').\n"
                "Avoid using NOW(), CURDATE(), or relative expressions like 'last 3 months'.\n"
                "You must not mention the year 2006 in the business question or answer — only use it silently in SQL filters.\n"
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
                cleaned_raw = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", raw.strip())
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

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
