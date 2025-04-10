from dotenv import load_dotenv
load_dotenv()

import os
import logging
from pathlib import Path
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, MetaData
from openai import OpenAI
from fasthtml.common import fast_app

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

from starlette.routing import Mount
app.router.routes.append(
    Mount("/static", app=StaticFiles(directory=static_path), name="static")
)


# Enable CORS for frontend running on a different port if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict to ["http://localhost:3000"] later
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

def generate_analysis_prompt(company_name, company_description, job_title, job_responsibilities, schema_str):
    return (
        f"Company Name: {company_name}\n"
        f"Company Description: {company_description}\n"
        f"Job Title: {job_title}\n"
        f"Job Responsibilities: {job_responsibilities}\n\n"
        f"Given the following SQL database schema:\n{schema_str}\n\n"
        f"Generate 5 insightful analytical questions that someone in this job would ask to help the company.\n"
        f"For each question, include:\n"
        f"- SQL query\n- Visualization type (bar chart, line chart, pie chart, table)\n"
        f"Format like:\nQuestion: ...\nSQL: ...\nVisualization: ...\n"
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

def parse_questions_queries(response_text):
    lines = response_text.split('\n')
    questions, queries, visualizations = [], [], []
    for line in lines:
        if line.startswith("Question:"):
            questions.append(line.replace("Question:", "").strip())
        elif line.startswith("SQL:"):
            queries.append(line.replace("SQL:", "").strip())
        elif line.startswith("Visualization:"):
            visualizations.append(line.replace("Visualization:", "").strip())
    return questions, queries, visualizations

def execute_query(query):
    with engine.connect() as connection:
        try:
            result = connection.execute(query)
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
    schema_str = get_db_schema()
    prompt = generate_analysis_prompt(
        data.company_name,
        data.company_description,
        data.job_title,
        data.job_responsibilities,
        schema_str
    )
    openai_response = ask_openai(prompt)
    questions, queries, visualizations = parse_questions_queries(openai_response)
    results = [execute_query(query) for query in queries]
    results_text = "\n".join([f"Question: {q}\nResult: {str(res)}" for q, (res, _) in zip(questions, results)])
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
        "results": [res for res, _ in results],
        "summary": summary
    }

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
