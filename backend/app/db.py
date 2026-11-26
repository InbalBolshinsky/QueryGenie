"""Read-only access to the SQLite database the agent analyses."""

import sqlite3
import time
import urllib.request
from pathlib import Path

NORTHWIND_URL = "https://raw.githubusercontent.com/jpwhite3/northwind-SQLite3/main/dist/northwind.db"


class QueryError(Exception):
    pass


class Database:
    def __init__(self, path: Path, timeout_s: float = 10.0):
        self.path = path
        self.timeout_s = timeout_s

    def _connect(self) -> sqlite3.Connection:
        # mode=ro makes writes impossible at the SQLite level, whatever the SQL says.
        return sqlite3.connect(f"file:{self.path}?mode=ro", uri=True)

    def schema(self) -> str:
        """Compact, LLM-friendly description of every table and its relationships."""
        lines = []
        with self._connect() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
            for (table,) in tables:
                cols = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
                fks = conn.execute(f'PRAGMA foreign_key_list("{table}")').fetchall()
                col_text = ", ".join(f"{c[1]} {c[2]}" for c in cols)
                lines.append(f'"{table}"({col_text})')
                lines += [f'  "{table}".{fk[3]} -> "{fk[2]}".{fk[4]}' for fk in fks]
        return "\n".join(lines)

    def query(self, sql: str, max_rows: int = 200) -> tuple[list[str], list[dict], bool]:
        """Run one read-only statement. Returns (columns, rows, truncated)."""
        if not sql.lstrip().lower().startswith(("select", "with")):
            raise QueryError("Only SELECT queries are allowed.")

        deadline = time.monotonic() + self.timeout_s
        conn = self._connect()
        # Abort runaway queries (e.g. accidental cross joins).
        conn.set_progress_handler(lambda: time.monotonic() > deadline, 10_000)
        try:
            cursor = conn.execute(sql)
            columns = [d[0] for d in cursor.description]
            raw = cursor.fetchmany(max_rows + 1)
        except sqlite3.Error as e:
            message = "Query timed out." if "interrupted" in str(e) else str(e)
            raise QueryError(message) from e
        finally:
            conn.close()

        rows = [
            {col: ("<binary>" if isinstance(val, bytes) else val) for col, val in zip(columns, row)}
            for row in raw[:max_rows]
        ]
        return columns, rows, len(raw) > max_rows


def ensure_northwind(path: Path) -> None:
    """Download the Northwind demo database on first run."""
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".download")
    print(f"Downloading Northwind demo database to {path} ...")
    urllib.request.urlretrieve(NORTHWIND_URL, tmp)
    tmp.rename(path)
