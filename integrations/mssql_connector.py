"""
AI Analytics Agent — MS SQL Server Connector
Secure connection management for MS SQL Server data source.
"""
import logging
from typing import Optional
import pandas as pd
from config import settings

logger = logging.getLogger(__name__)


class MSSQLConnector:
    def __init__(self):
        self.connection_string = settings.mssql_connection_string
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            from sqlalchemy import create_engine
            self._engine = create_engine(self.connection_string, pool_pre_ping=True, pool_size=5)
        return self._engine

    def query(self, sql: str) -> pd.DataFrame:
        return pd.read_sql(sql, self._get_engine())

    def test_connection(self) -> bool:
        try:
            from sqlalchemy import text
            engine = self._get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"MSSQL connection failed: {e}")
            return False

    def close(self):
        if self._engine:
            self._engine.dispose()
            self._engine = None

