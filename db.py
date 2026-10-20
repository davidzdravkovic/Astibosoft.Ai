from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg
from pgvector.psycopg import register_vector

from config import settings


@contextmanager
def connect() -> Iterator[psycopg.Connection]:
    with psycopg.connect(settings.dsn) as conn:
        # Required before register_vector; also applied by deploy/docker-init.sh
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.commit()
        register_vector(conn)
        yield conn
