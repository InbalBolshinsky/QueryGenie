from dotenv import load_dotenv
load_dotenv()  # This loads variables from your .env file

from fasthtml.common import *  # Ensure that the 'fasthtml' module is in your PYTHONPATH
from fastapi import Response, Request
from openai import OpenAI
from sqlalchemy import create_engine, MetaData
import os

# Initialize the FastHTML app (which sets up routing)
app, rt = fast_app()

# Set up the OpenAI client using the API key from the environment variables
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Route to Serve the Frontend (index.html) ---

@rt("/")
def index():
    # Adjust the path to where your index.html is located relative to this file.
    index_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return Response(content=html_content, media_type="text/html")

# --- Helper Functions ---

def get_responsibilities(organization, job_role):
    prompt = f"What are the typical responsibilities of a {job_role} in a {organization}?"
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def get_db_schema(db_conn):
    engine = create_engine(db_conn)
    metadata = MetaData()
    metadata.reflect(engine)
    schema_str = ""
    for table in metadata.tables.values():
        schema_str += f"Table: {table.name}\n"
        for column in table.columns:
            schema_str += f"  - {column.name} ({column.type})\n"
    return schema_str

def get_analytical_questions(organization, job_role, responsibilities, schema_str):
    prompt = (
        f"Given the following database schema:\n{schema_str}\n"
        f"What are the top 5 analytical questions a {job_role} in a {organization} might ask "
        f"to gain insights into the business?\n"
        f"For each question, provide an SQL query and suggest a visualization type (bar chart, line chart, pie chart, table).\n"
        f"Format your response with lines starting with 'Question:', 'SQL:' and 'Visualization:' as needed."
    )
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

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

def execute_query(db_conn, query):
    engine = create_engine(db_conn)
    with engine.connect() as connection:
        try:
            result = connection.execute(query)
            return result.fetchall(), result.keys()
        except Exception as e:
            return str(e), []

def get_summary(results_text):
    prompt = f"Based on the following data analysis results:\n{results_text}\nWhat are the key insights or conclusions that can be derived?"
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# --- API Endpoint for Analysis ---

@rt("/analyze", methods=["POST"])
def analyze(organization: str, job_role: str, db_conn: str):
    # Step 1: Get responsibilities using OpenAI
    responsibilities = get_responsibilities(organization, job_role)
    
    # Step 2: Retrieve the database schema
    schema_str = get_db_schema(db_conn)
    
    # Step 3: Get analytical questions, SQL queries, and visualization suggestions
    analytical_response = get_analytical_questions(organization, job_role, responsibilities, schema_str)
    questions, queries, visualizations = parse_questions_queries(analytical_response)
    
    # Step 4: Execute each SQL query
    results = [execute_query(db_conn, query) for query in queries]
    
    # Step 5: Compile a text summary from the questions and results for further summarization
    results_text = "\n".join([f"Question: {q}\nResult: {str(res)}" for q, (res, _) in zip(questions, results)])
    
    # Step 6: Get a summary of insights from OpenAI based on the query results
    summary = get_summary(results_text)
    
    # Return a JSON response (could be used by your frontend)
    return {
        "organization": organization,
        "job_role": job_role,
        "responsibilities": responsibilities,
        "schema": schema_str,
        "questions": questions,
        "queries": queries,
        "results": [str(res) for res, _ in results],
        "summary": summary
    }

# --- Run the App with uvicorn ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
