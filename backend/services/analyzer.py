import json
import logging
import re
from sqlalchemy import MetaData, text
from functools import lru_cache
from openai import OpenAI

class AnalyzerService:
    def __init__(self, engine, openai_client: OpenAI):
        self.engine = engine
        self.openai = openai_client

    @lru_cache(maxsize=1)
    def get_db_schema(self):
        metadata = MetaData()
        metadata.reflect(self.engine)
        schema_str = ""
        for table in metadata.tables.values():
            schema_str += f"Table: {table.name}\n"
            for column in table.columns:
                schema_str += f"  - {column.name} ({column.type})\n"
        return schema_str

    def ask_openai(self, prompt: str) -> str:
        try:
            response = self.openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"OpenAI error: {e}")
            return ""

    def execute_query(self, query: str):
        with self.engine.connect() as conn:
            try:
                result = conn.execute(text(query))
                return [dict(zip(result.keys(), row)) for row in result.fetchall()], result.keys()
            except Exception as e:
                logging.error(f"SQL execution error: {e}")
                return str(e), []

    def get_summary(self, results_text: str) -> str:
        if "error" in results_text.lower():
            return "Some queries failed; unable to provide a reliable summary."
        summary_prompt = (
            "Assume today is December 31, 2006.\n"
            "You are writing a final business summary report for a stakeholder.\n"
            "Write a structured and complete list of 5 bullet-point insights based only on the following results:\n\n"
            f"{results_text}\n\n"
            "Write clearly and do NOT repeat the year 2006. Do not trail off. Finish each bullet point with a full sentence."
        )
        return self.ask_openai(summary_prompt)

    def clean_json_response(self, raw):
        try:
            cleaned_raw = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", raw.strip())
            return json.loads(cleaned_raw)
        except Exception as e:
            logging.warning(f"Failed to parse GPT response: {e}")
            return None
