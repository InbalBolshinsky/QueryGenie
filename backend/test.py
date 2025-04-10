# test_schema.py

from sqlalchemy import create_engine, MetaData
from dotenv import load_dotenv
import os

load_dotenv()

def get_db_schema(db_conn):
    engine = create_engine(db_conn)
    metadata = MetaData()
    metadata.reflect(engine)
    schema_str = ""
    for table in metadata.tables.values():
        schema_str += f"\nTable: {table.name}\n"
        for column in table.columns:
            schema_str += f"  - {column.name} ({column.type})\n"
    return schema_str

if __name__ == "__main__":
    db_conn = os.getenv("DATABASE_URL")
    schema = get_db_schema(db_conn)
    print(schema)
