from __future__ import annotations

import logging
from pathlib import Path

from db import connect

logger = logging.getLogger(__name__)

SQL_DIR = Path(__file__).resolve().parent / "sql"


def apply_migrations() -> None:
    scripts = sorted(SQL_DIR.glob("*.sql"))
    if not scripts:
        logger.warning("No SQL migrations found in %s", SQL_DIR)
        return

    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS "AiSchemaVersions" (
                "Version" integer PRIMARY KEY,
                "Name" text NOT NULL,
                "AppliedAt" timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        conn.commit()

        applied = {
            row[0]
            for row in conn.execute('SELECT "Version" FROM "AiSchemaVersions"').fetchall()
        }

        for script in scripts:
            version = int(script.name.split("_", 1)[0])
            if version in applied:
                continue

            sql = script.read_text(encoding="utf-8")
            logger.info("Applying Ai migration %s (%s)", version, script.name)
            for statement in _statements(sql):
                conn.execute(statement)
            conn.execute(
                """
                INSERT INTO "AiSchemaVersions" ("Version", "Name")
                VALUES (%s, %s)
                """,
                (version, script.name),
            )
            conn.commit()
            logger.info("Applied Ai migration %s", version)


def _statements(sql: str) -> list[str]:
    parts: list[str] = []
    for raw in sql.split(";"):
        statement = raw.strip()
        if not statement or statement.startswith("--"):
            continue
        parts.append(statement)
    return parts
