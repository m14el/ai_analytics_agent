"""
AI Analytics Agent — ETL Transform Module
Data cleaning, validation, and metric calculations.
"""

import logging
from typing import Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def clean_data(data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Clean all DataFrames:
    - Remove exact duplicates
    - Handle null values
    - Normalize types
    """
    cleaned = {}
    for name, df in data.items():
        original_len = len(df)
        # Remove duplicates
        df = df.drop_duplicates()
        dupes_removed = original_len - len(df)
        if dupes_removed:
            logger.info(f"  {name}: removed {dupes_removed} duplicates")

        # Handle nulls per entity
        if name == "tasks":
            df["actual_hours"] = df["actual_hours"].fillna(0)
            df["estimated_hours"] = df["estimated_hours"].fillna(0)
            df["reopen_count"] = df["reopen_count"].fillna(0).astype(int)
            df["comments_count"] = df["comments_count"].fillna(0).astype(int)
        elif name == "financials":
            for col in ["revenue", "costs", "labor_costs", "overhead_costs"]:
                df[col] = df[col].fillna(0)
        elif name == "developers":
            df["hourly_rate"] = df["hourly_rate"].fillna(0)
            df["monthly_salary"] = df["monthly_salary"].fillna(0)

        cleaned[name] = df
        logger.info(f"  {name}: cleaned — {len(df)} records")

    return cleaned


def calculate_financial_metrics(financials: pd.DataFrame) -> pd.DataFrame:
    """Add profit and margin columns to financial data."""
    df = financials.copy()
    df["profit"] = df["revenue"] - df["costs"]
    df["margin"] = np.where(
        df["revenue"] > 0,
        (df["profit"] / df["revenue"]) * 100,
        0.0
    )
    return df


def aggregate_project_metrics(
    financials: pd.DataFrame,
    projects: pd.DataFrame,
    tasks: pd.DataFrame,
    developers: pd.DataFrame,
) -> pd.DataFrame:
    """
    Aggregate financial + task data per project.
    Returns a DataFrame with one row per project and computed metrics.
    """
    # Financial aggregation
    fin_agg = financials.groupby("project_id").agg(
        total_revenue=("revenue", "sum"),
        total_costs=("costs", "sum"),
        total_labor_costs=("labor_costs", "sum"),
        total_overhead_costs=("overhead_costs", "sum"),
        total_profit=("profit", "sum"),
        avg_margin=("margin", "mean"),
        months_count=("period", "count"),
    ).reset_index()

    # Task aggregation
    task_agg = tasks.groupby("project_id").agg(
        task_count=("id", "count"),
        total_estimated_hours=("estimated_hours", "sum"),
        total_actual_hours=("actual_hours", "sum"),
        total_reopens=("reopen_count", "sum"),
        total_comments=("comments_count", "sum"),
        completed_tasks=("status", lambda x: (x == "done").sum()),
    ).reset_index()

    # Merge
    result = projects[["id", "name", "project_type", "client", "stack", "status"]].copy()
    result = result.merge(fin_agg, left_on="id", right_on="project_id", how="left")
    result = result.merge(task_agg, left_on="id", right_on="project_id", how="left",
                          suffixes=("", "_task"))

    # Fill NaN
    numeric_cols = result.select_dtypes(include=[np.number]).columns
    result[numeric_cols] = result[numeric_cols].fillna(0)

    # Derived metrics
    result["burn_rate"] = np.where(
        result["months_count"] > 0,
        result["total_costs"] / result["months_count"],
        0.0
    )
    result["revenue_per_hour"] = np.where(
        result["total_actual_hours"] > 0,
        result["total_revenue"] / result["total_actual_hours"],
        0.0
    )
    result["overtime_ratio"] = np.where(
        result["total_estimated_hours"] > 0,
        result["total_actual_hours"] / result["total_estimated_hours"],
        0.0
    )
    result["reopen_rate"] = np.where(
        result["task_count"] > 0,
        result["total_reopens"] / result["task_count"],
        0.0
    )
    result["margin"] = np.where(
        result["total_revenue"] > 0,
        (result["total_profit"] / result["total_revenue"]) * 100,
        0.0
    )

    # Status: green (margin > 15%), yellow (0-15%), red (< 0%)
    result["profitability_status"] = np.select(
        [result["margin"] > 15, result["margin"] > 0],
        ["green", "yellow"],
        default="red"
    )

    return result


def aggregate_stack_metrics(project_metrics: pd.DataFrame) -> pd.DataFrame:
    """Aggregate metrics by technology stack."""
    agg = project_metrics.groupby("stack").agg(
        project_count=("id", "count"),
        total_revenue=("total_revenue", "sum"),
        total_costs=("total_costs", "sum"),
        total_profit=("total_profit", "sum"),
        total_hours=("total_actual_hours", "sum"),
        avg_burn_rate=("burn_rate", "mean"),
    ).reset_index()

    agg["margin"] = np.where(
        agg["total_revenue"] > 0,
        (agg["total_profit"] / agg["total_revenue"]) * 100,
        0.0
    )
    agg["avg_revenue_per_hour"] = np.where(
        agg["total_hours"] > 0,
        agg["total_revenue"] / agg["total_hours"],
        0.0
    )
    agg["status"] = np.select(
        [agg["margin"] > 15, agg["margin"] > 0],
        ["green", "yellow"],
        default="red"
    )

    return agg.sort_values("margin", ascending=True)


def aggregate_task_type_metrics(
    tasks: pd.DataFrame, developers: pd.DataFrame
) -> pd.DataFrame:
    """Aggregate metrics by task type."""
    # Merge task with developer rate
    merged = tasks.merge(
        developers[["id", "hourly_rate"]],
        left_on="developer_id", right_on="id",
        how="left", suffixes=("", "_dev")
    )
    merged["hourly_rate"] = merged["hourly_rate"].fillna(0)
    merged["cost"] = merged["actual_hours"] * merged["hourly_rate"]

    agg = merged.groupby("task_type").agg(
        task_count=("id", "count"),
        total_estimated_hours=("estimated_hours", "sum"),
        total_actual_hours=("actual_hours", "sum"),
        total_cost=("cost", "sum"),
        total_reopens=("reopen_count", "sum"),
        total_comments=("comments_count", "sum"),
    ).reset_index()

    agg["overtime_ratio"] = np.where(
        agg["total_estimated_hours"] > 0,
        agg["total_actual_hours"] / agg["total_estimated_hours"],
        0.0
    )
    agg["reopen_rate"] = np.where(
        agg["task_count"] > 0,
        agg["total_reopens"] / agg["task_count"],
        0.0
    )
    agg["status"] = np.select(
        [agg["overtime_ratio"] <= 1.1, agg["overtime_ratio"] <= 1.3],
        ["green", "yellow"],
        default="red"
    )

    return agg.sort_values("overtime_ratio", ascending=False)


def aggregate_developer_metrics(
    tasks: pd.DataFrame, developers: pd.DataFrame
) -> pd.DataFrame:
    """Calculate per-developer efficiency metrics."""
    task_agg = tasks.groupby("developer_id").agg(
        total_estimated=("estimated_hours", "sum"),
        total_actual=("actual_hours", "sum"),
        tasks_total=("id", "count"),
        tasks_completed=("status", lambda x: (x == "done").sum()),
        total_reopens=("reopen_count", "sum"),
    ).reset_index()

    result = developers[["id", "name", "role", "stack", "hourly_rate"]].merge(
        task_agg, left_on="id", right_on="developer_id", how="left"
    )
    numeric_cols = result.select_dtypes(include=[np.number]).columns
    result[numeric_cols] = result[numeric_cols].fillna(0)

    result["total_cost"] = result["total_actual"] * result["hourly_rate"]
    result["estimation_accuracy"] = np.where(
        result["total_actual"] > 0,
        result["total_estimated"] / result["total_actual"],
        0.0
    )
    result["overtime_ratio"] = np.where(
        result["total_estimated"] > 0,
        result["total_actual"] / result["total_estimated"],
        0.0
    )
    result["velocity"] = np.where(
        result["total_actual"] > 0,
        result["tasks_completed"] / (result["total_actual"] / 160),  # per month equiv
        0.0
    )
    # Efficiency score: weighted composite
    result["efficiency_score"] = (
        result["estimation_accuracy"].clip(0, 1.5) * 40 +
        (1 - result["overtime_ratio"].clip(0, 2) / 2) * 30 +
        np.where(result["tasks_total"] > 0,
                 (1 - result["total_reopens"] / result["tasks_total"]) * 30,
                 30)
    )

    return result


def transform(data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Main transform function — runs the full transformation pipeline.
    Returns enriched DataFrames ready for loading.
    """
    logger.info("Starting data transformation...")

    # 1. Clean
    data = clean_data(data)

    # 2. Calculate financial metrics
    data["financials"] = calculate_financial_metrics(data["financials"])
    logger.info("  Financial metrics calculated")

    # 3. Project-level aggregation
    data["project_metrics"] = aggregate_project_metrics(
        data["financials"], data["projects"], data["tasks"], data["developers"]
    )
    logger.info(f"  Project metrics: {len(data['project_metrics'])} projects")

    # 4. Stack aggregation
    data["stack_metrics"] = aggregate_stack_metrics(data["project_metrics"])
    logger.info(f"  Stack metrics: {len(data['stack_metrics'])} stacks")

    # 5. Task type aggregation
    data["task_type_metrics"] = aggregate_task_type_metrics(
        data["tasks"], data["developers"]
    )
    logger.info(f"  Task type metrics: {len(data['task_type_metrics'])} types")

    # 6. Developer metrics
    data["developer_metrics"] = aggregate_developer_metrics(
        data["tasks"], data["developers"]
    )
    logger.info(f"  Developer metrics: {len(data['developer_metrics'])} devs")

    return data
