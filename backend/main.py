from fasthtml.common import *    # Your FastHTML code (if this is needed for routing)
from openai import OpenAI
from sqlalchemy import create_engine, MetaData
import os
import json

# Initialize the app (you can still use FastHTML for routing if desired)
app, rt = fast_app()

# Set up OpenAI using your API key from the environment
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Helper Functions (same as before) ---

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
def post(organization: str, job_role: str, db_conn: str):
    # Step 1: Get responsibilities using OpenAI
    responsibilities = get_responsibilities(organization, job_role)
    # Step 2: Retrieve the database schema
    schema_str = get_db_schema(db_conn)
    # Step 3: Get analytical questions and SQL queries
    analytical_response = get_analytical_questions(organization, job_role, responsibilities, schema_str)
    questions, queries, visualizations = parse_questions_queries(analytical_response)
    # Step 4: Execute the SQL queries and obtain results
    results = [execute_query(db_conn, query) for query in queries]
    # Create a simple results text summary for further summarization
    results_text = "\n".join([f"Question: {q}\nResult: {str(res)}" for q, (res, _) in zip(questions, results)])
    # Step 5: Get a summary of insights from OpenAI
    summary = get_summary(results_text)
    # Return JSON (or you could format as HTML fragments)
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

if __name__ == "__main__":
    app.run()
