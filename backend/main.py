from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from openai import OpenAI
from pydantic import BaseModel
import os
import logging
import json

from services.analyzer import AnalyzerService
from prompts.business_prompt import generate_prompt

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

# Dependencies
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
db_engine = create_engine(os.getenv("DATABASE_URL"))
analyzer = AnalyzerService(db_engine, openai_client)

# Request model
class AnalyzeRequest(BaseModel):
    company_name: str
    company_description: str
    job_title: str
    job_responsibilities: str

# --- API Endpoints ---
@app.get("/schema")
def schema_preview():
    return {"schema": analyzer.get_db_schema()}

@app.post("/analyze")
def analyze(data: AnalyzeRequest):
    try:
        schema_str = analyzer.get_db_schema()
        questions, queries, visualizations, results = [], [], [], []
        seen_q, seen_sql = set(), set()
        attempts, max_attempts = 0, 15

        while len(questions) < 5 and attempts < max_attempts:
            attempts += 1

            prompt = generate_prompt(
                data.company_name,
                data.company_description,
                data.job_title,
                data.job_responsibilities,
                schema_str
            )

            raw = analyzer.ask_openai(prompt)
            logging.info(f"🔎 Raw GPT Response:\n{raw}")

            parsed = analyzer.clean_json_response(raw)
            if not parsed:
                continue

            q = parsed["question"].strip()
            sql = ' '.join(parsed["sql"].split()).strip()
            viz = parsed["visualization"].strip()

            if not sql or q in seen_q or sql in seen_sql:
                continue

            res, _ = analyzer.execute_query(sql)
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
        summary = analyzer.get_summary(combined)

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