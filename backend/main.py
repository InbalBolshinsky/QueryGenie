from dotenv import load_dotenv
from pathlib import Path
# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

import os
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

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app with fasthtml
app = FastAPI()

def rt(path: str, methods=["GET"]):
    def decorator(func):
        app.api_route(path, methods=methods)(func)
        return func
    return decorator

# Mount static files (JS, CSS, etc.)
static_path = Path(__file__).parent.parent / "frontend" / "static"
print(">>> Static path:", static_path)
print(">>> Exists:", static_path.exists())

print(">>> Static folder contents:")
if static_path.exists():
    for file in static_path.iterdir():
        print("   -", file.name)

app.router.routes.append(
    Mount("/static", app=StaticFiles(directory=static_path), name="static")
)

@app.get("/GenieLamp.ico")
async def favicon():
    return FileResponse(static_path / "GenieLamp.ico")

# Enable CORS for frontend running on a different port if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the index.html
@rt("/")
def index():
    index_path = Path(__file__).parent.parent / "frontend" / "index.html"
    with open(index_path, "r", encoding="utf-8") as f:
        return Response(content=f.read(), media_type="text/html")

# Set up OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Database connection
DB_CONN = os.getenv("DATABASE_URL")
engine = create_engine(DB_CONN)

# Pydantic request model
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

def generate_single_insight_prompt(company_name, company_description, job_title, job_responsibilities, schema_str):
    return (
        f"You are a senior data analyst and MySQL expert.\n\n"
        f"Company Name: {company_name}\n"
        f"Company Description: {company_description}\n"
        f"Job Title: {job_title}\n"
        f"Job Responsibilities: {job_responsibilities}\n\n"
        f"Here is the database schema:\n{schema_str}\n\n"
        f"Your task: Generate one business insight relevant to this job. Return a JSON object with:\n"
        f"- `question`: the business question\n"
        f"- `sql`: a syntactically valid MySQL query\n"
        f"- `visualization`: a recommended chart type (Bar Chart, Line Chart, Pie Chart, etc.)\n\n"
        f"⚠️ Use only tables and columns from the schema.\n"
        f"⚠️ Always use full table names (no aliases).\n"
        f"⚠️ Put JOINs before WHERE clauses.\n"
        f"⚠️ Return only a single JSON object, no text, no markdown, no explanation.\n\n"
        f"Example:\n"
        f"{{\n"
        f"  \"question\": \"What are the top 5 products by revenue?\",\n"
        f"  \"sql\": \"SELECT ...\",\n"
        f"  \"visualization\": \"Bar Chart\"\n"
        f"}}"
    )

def ask_openai(prompt):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        return ""

    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse GPT response as JSON: {e}")
        return [], [], []

def execute_query(query):
    with engine.connect() as connection:
        try:
            result = connection.execute(text(query))
            return [dict(zip(result.keys(), row)) for row in result.fetchall()], result.keys()
        except Exception as e:
            logging.error(f"SQL execution error: {e}")
            return str(e), []

def get_summary(results_text):
    if "error" in results_text.lower():
        return "Some queries failed; unable to provide a reliable summary."
    prompt = f"Based on the following data analysis results:\n{results_text}\nWhat are the key insights or conclusions that can be derived?"
    return ask_openai(prompt)

# --- API Endpoints ---
@rt("/schema")
def schema_preview():
    return {"schema": get_db_schema()}

@rt("/analyze", methods=["POST"])
def analyze(data: AnalyzeRequest):
    try:
        schema_str = get_db_schema()

        questions, queries, visualizations, results = [], [], [], []
        seen_questions, seen_queries = set(), set()
        attempts = 0
        max_attempts = 15

        while len(questions) < 5 and attempts < max_attempts:
            prompt = (
                f"You are a senior data analyst and MySQL expert.\n\n"
                f"Company Name: {data.company_name}\n"
                f"Company Description: {data.company_description}\n"
                f"Job Title: {data.job_title}\n"
                f"Job Responsibilities: {data.job_responsibilities}\n\n"
                f"Here is the database schema:\n{schema_str}\n\n"
                f"Your task: Generate ONE business question relevant to this job. Return a JSON object with:\n"
                f"- `question`: the business question\n"
                f"- `sql`: a syntactically valid MySQL query using only the schema\n"
                f"- `visualization`: a recommended chart type (Bar Chart, Line Chart, Pie Chart, etc.)\n\n"
                f"⚠️ Use only columns and tables from the schema.\n"
                f"⚠️ Always use full table names (no aliases).\n"
                f"⚠️ Always put JOINs before WHERE clauses.\n"
                f"⚠️ Return only a JSON object. No text, no markdown, no explanation."
            )

            insight = ask_openai(prompt)
            attempts += 1

            try:
                parsed = json.loads(insight)
                question = parsed.get("question", "").strip()
                sql = parsed.get("sql", "").strip()
                viz = parsed.get("visualization", "").strip()
            except Exception:
                logging.warning("Failed to parse GPT response. Retrying...")
                continue

            if not sql or question in seen_questions or sql in seen_queries:
                continue

            result, keys = execute_query(sql)
            if isinstance(result, str) or not result:
                logging.info("Empty or failed result, retrying...")
                continue

            questions.append(question)
            queries.append(sql)
            visualizations.append(viz)
            results.append(result)
            seen_questions.add(question)
            seen_queries.add(sql)

        results_text = "\n".join([
            f"Question: {q}\nResult: {str(res)}"
            for q, res in zip(questions, results)
        ])
        summary = get_summary(results_text)

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
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# --- Run the app ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

def func():
    northwind_schema = get_db_schema()
    northwind_schema = northwind_schema.replace("  ", " ").replace("\n", " ").strip()
    northwind_schema = northwind_schema[:3000] + "..." if len(northwind_schema) > 3000 else northwind_schema
    return (
        f"Company Name: Northwind\n"
        f"Company Description: Northwind Traders is a mid-sized wholesale and distribution company specializing in gourmet food products."
        f"The company supplies restaurants, cafés, grocery stores, and specialty food retailers with a diverse range of food products.\n"
        f"Job Title: Sales Manager\n"
        f"Job Responsibilities: As a Sales Manager at Northwind Traders, my job is to grow revenue, manage my team, and keep our customers happy."
        f"I track my team’s performance across different regions to make sure we’re hitting our targets.\n\n"
        f"Given the following SQL database schema:\n{northwind_schema[:3000]}...\n\n"
        f"Generate 5 insightful analytical questions that someone in this job would ask to help the company.\n"
        f"For each question, include:\n"
        f"- SQL query\n- Visualization type (bar chart, line chart, pie chart, table)\n"
        f"Format like:\nQuestion: ...\nSQL: ...\nVisualization: ...\n"
    )