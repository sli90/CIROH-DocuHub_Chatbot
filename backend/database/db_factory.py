"""Selects the DB backend so call sites (backend/rag/ask.py) never branch on it.

DB_BACKEND=psycopg2 (default)   -> DatabaseManager, direct TCP to Azure/any Postgres.
DB_BACKEND=rds_data_api         -> RdsDataApiManager, Aurora Serverless v2 over HTTPS.

Both implement the same `with Manager() as db: db.execute_query(...)` shape,
so this is the only place that needs to know which one is active.
"""

from __future__ import annotations

import os


def get_db_manager():
    backend = os.getenv("DB_BACKEND", "psycopg2").lower()
    if backend == "rds_data_api":
        from .rds_data_client import RdsDataApiManager

        return RdsDataApiManager()
    from .database import DatabaseManager

    return DatabaseManager()
