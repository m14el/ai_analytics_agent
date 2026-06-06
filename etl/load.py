"""
AI Analytics Agent — ETL Load Module
Loads transformed data into the analytical database.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict

import pandas as pd
from sqlalchemy.orm import Session

from models.database import (
    SessionLocal, init_db,
    Project, Developer, Task, Financial, AnalyticsSnapshot,
    DeveloperAssignment,
)

logger = logging.getLogger(__name__)


def _clear_tables(session: Session):
    """Clear all analytical tables before full reload."""
    for model in [DeveloperAssignment, Task, Financial, Developer, Project]:
        session.query(model).delete()
    session.commit()
    logger.info("  Cleared existing data")


def _safe_date(val):
    """Convert pandas Timestamp/NaT to Python date or None."""
    if pd.isna(val):
        return None
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None


def _safe_str(val):
    """Convert NaN strings to None."""
    if pd.isna(val):
        return None
    return str(val)


def load_projects(session: Session, df: pd.DataFrame):
    """Load projects into the database."""
    for _, row in df.iterrows():
        project = Project(
            id=int(row["id"]),
            name=row["name"],
            project_type=_safe_str(row.get("project_type")),
            client=_safe_str(row.get("client")),
            stack=_safe_str(row.get("stack")),
            status=_safe_str(row.get("status")) or "active",
            start_date=_safe_date(row.get("start_date")),
            end_date=_safe_date(row.get("end_date")),
        )
        session.merge(project)
    session.commit()
    logger.info(f"  Loaded {len(df)} projects")


def load_developers(session: Session, df: pd.DataFrame):
    """Load developers into the database."""
    for _, row in df.iterrows():
        dev = Developer(
            id=int(row["id"]),
            name=row["name"],
            role=row.get("role"),
            stack=row.get("stack"),
            hourly_rate=float(row.get("hourly_rate", 0)),
            monthly_salary=float(row.get("monthly_salary", 0)),
        )
        session.merge(dev)
    session.commit()
    logger.info(f"  Loaded {len(df)} developers")


def load_tasks(session: Session, df: pd.DataFrame):
    """Load tasks into the database."""
    for _, row in df.iterrows():
        task = Task(
            id=int(row["id"]),
            external_id=_safe_str(row.get("external_id")),
            title=row["title"],
            description=_safe_str(row.get("description")),
            task_type=_safe_str(row.get("task_type")),
            status=_safe_str(row.get("status")),
            priority=_safe_str(row.get("priority")),
            project_id=int(row.get("project_id", 0)) or None,
            developer_id=int(row.get("developer_id", 0)) or None,
            estimated_hours=float(row.get("estimated_hours", 0)),
            actual_hours=float(row.get("actual_hours", 0)),
            reopen_count=int(row.get("reopen_count", 0)),
            comments_count=int(row.get("comments_count", 0)),
            created_date=_safe_date(row.get("created_date")),
            completed_date=_safe_date(row.get("completed_date")),
        )
        session.merge(task)
    session.commit()
    logger.info(f"  Loaded {len(df)} tasks")


def load_financials(session: Session, df: pd.DataFrame):
    """Load financial records into the database."""
    for _, row in df.iterrows():
        fin = Financial(
            id=int(row["id"]),
            project_id=int(row["project_id"]),
            period=_safe_date(row["period"]),
            revenue=float(row.get("revenue", 0)),
            costs=float(row.get("costs", 0)),
            labor_costs=float(row.get("labor_costs", 0)),
            overhead_costs=float(row.get("overhead_costs", 0)),
            profit=float(row.get("profit", 0)),
            margin=float(row.get("margin", 0)),
        )
        session.merge(fin)
    session.commit()
    logger.info(f"  Loaded {len(df)} financial records")


def save_analytics_snapshot(session: Session, data: Dict[str, pd.DataFrame]):
    """Save aggregated metrics as a JSON snapshot for historical tracking."""
    snapshot_data = {}
    for key in ["project_metrics", "stack_metrics", "task_type_metrics", "developer_metrics"]:
        if key in data:
            snapshot_data[key] = data[key].to_dict(orient="records")

    snapshot = AnalyticsSnapshot(
        snapshot_date=datetime.now(timezone.utc),
        snapshot_type="etl_run",
        data_json=json.dumps(snapshot_data, default=str),
    )
    session.add(snapshot)
    session.commit()
    logger.info("  Saved analytics snapshot")


def load(data: Dict[str, pd.DataFrame]):
    """
    Main load function — saves all data to the analytical database.
    Performs a full reload (clear + insert).
    """
    logger.info("Starting data load...")

    # Ensure tables exist
    init_db()

    session = SessionLocal()
    try:
        _clear_tables(session)

        load_projects(session, data["projects"])
        load_developers(session, data["developers"])
        load_tasks(session, data["tasks"])
        load_financials(session, data["financials"])
        save_analytics_snapshot(session, data)

        logger.info("Data load completed successfully")
    except Exception as e:
        session.rollback()
        logger.error(f"Data load failed: {e}")
        raise
    finally:
        session.close()
