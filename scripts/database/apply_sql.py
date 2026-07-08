"""Aplica en la base el SQL offline de Alembic (alembic.sql)
usando SQLAlchemy: detecta encoding, separa por “;” y ejecuta
todo dentro de una transacción."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv()

from app.infra.persistence.database import ENGINE  # noqa: E402

SQL_FILE = ROOT / "alembic.sql"


def iter_statements(sql_text: str):
    """
    Generador que separa el texto SQL en statements individuales.
    Corta cada vez que encuentra un ';' al final de línea.
    Además saltea la línea de DSN que algunos entornos imprimen.
    """
    buf = []
    for line in sql_text.splitlines():
        if line.startswith("[DB] Using:"):
            continue
        buf.append(line)
        if line.strip().endswith(";"):
            stmt = "\n".join(buf).strip()
            if stmt:
                yield stmt
            buf = []
    tail = "\n".join(buf).strip()
    if tail:
        yield tail


def main() -> int:
    if not SQL_FILE.exists():
        print(f"[apply_sql] File not found: {SQL_FILE}")
        print(
            "Run:  .\\.venv\\Scripts\\python.exe -m alembic upgrade head --sql > alembic.sql"
        )
        return 2

    raw = SQL_FILE.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            sql_text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        print("[apply_sql] Could not decode alembic.sql with common encodings.")
        return 3
    stmts = list(iter_statements(sql_text))
    print(f"[apply_sql] Executing {len(stmts)} statements from {SQL_FILE.name}...")

    with ENGINE.begin() as conn:
        for i, stmt in enumerate(stmts, 1):
            conn.execute(text(stmt))
    print("[apply_sql] Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
