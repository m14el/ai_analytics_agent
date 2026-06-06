"""
AI Analytics Agent — ETL Extract Module
Extracts data from various sources: MS SQL Server, CSV files, demo data.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from config import settings

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent


class BaseExtractor:
    """Base class for data extractors."""

    def extract_projects(self) -> pd.DataFrame:
        raise NotImplementedError

    def extract_developers(self) -> pd.DataFrame:
        raise NotImplementedError

    def extract_tasks(self) -> pd.DataFrame:
        raise NotImplementedError

    def extract_financials(self) -> pd.DataFrame:
        raise NotImplementedError

    def extract_all(self) -> Dict[str, pd.DataFrame]:
        """Extract all data sources and return as a dict of DataFrames."""
        logger.info("Starting data extraction...")
        data = {
            "projects": self.extract_projects(),
            "developers": self.extract_developers(),
            "tasks": self.extract_tasks(),
            "financials": self.extract_financials(),
        }
        for name, df in data.items():
            logger.info(f"  Extracted {name}: {len(df)} records")
        return data


class DemoExtractor(BaseExtractor):
    """Extracts data from local CSV demo files."""

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir) if data_dir else BASE_DIR / "data" / "demo"

    def extract_projects(self) -> pd.DataFrame:
        return pd.read_csv(self.data_dir / "projects.csv")

    def extract_developers(self) -> pd.DataFrame:
        return pd.read_csv(self.data_dir / "developers.csv")

    def extract_tasks(self) -> pd.DataFrame:
        df = pd.read_csv(self.data_dir / "tasks.csv")
        # Parse dates
        for col in ["created_date", "completed_date"]:
            df[col] = pd.to_datetime(df[col], errors="coerce")
        return df

    def extract_financials(self) -> pd.DataFrame:
        df = pd.read_csv(self.data_dir / "financials.csv")
        df["period"] = pd.to_datetime(df["period"])
        return df


class MSSQLExtractor(BaseExtractor):
    """Extracts data from MS SQL Server."""

    def __init__(self):
        try:
            import importlib
            importlib.import_module("pyodbc")
            self.connection_string = settings.mssql_connection_string
        except ImportError:
            logger.warning("pyodbc not installed. MSSQL extraction unavailable.")
            self.connection_string = None

    def _query(self, sql: str) -> pd.DataFrame:
        if not self.connection_string:
            raise RuntimeError("MS SQL Server connection not configured")
        return pd.read_sql(sql, self.connection_string)

    def extract_projects(self) -> pd.DataFrame:
        return self._query("SELECT * FROM projects")

    def extract_developers(self) -> pd.DataFrame:
        return self._query("SELECT * FROM developers")

    def extract_tasks(self) -> pd.DataFrame:
        return self._query("SELECT * FROM tasks")

    def extract_financials(self) -> pd.DataFrame:
        return self._query("SELECT * FROM financials")


class CSVExtractor(BaseExtractor):
    """Extracts data from user-provided CSV files."""

    def __init__(self, projects_path: str, developers_path: str,
                 tasks_path: str, financials_path: str):
        self.paths = {
            "projects": Path(projects_path),
            "developers": Path(developers_path),
            "tasks": Path(tasks_path),
            "financials": Path(financials_path),
        }

    def extract_projects(self) -> pd.DataFrame:
        return pd.read_csv(self.paths["projects"])

    def extract_developers(self) -> pd.DataFrame:
        return pd.read_csv(self.paths["developers"])

    def extract_tasks(self) -> pd.DataFrame:
        df = pd.read_csv(self.paths["tasks"])
        for col in ["created_date", "completed_date"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df

    def extract_financials(self) -> pd.DataFrame:
        df = pd.read_csv(self.paths["financials"])
        if "period" in df.columns:
            df["period"] = pd.to_datetime(df["period"])
        return df


def get_extractor() -> BaseExtractor:
    """Factory function — returns the appropriate extractor based on config."""
    if settings.data_mode == "mssql":
        logger.info("Using MS SQL Server extractor")
        return MSSQLExtractor()
    else:
        logger.info("Using demo data extractor")
        return DemoExtractor()
