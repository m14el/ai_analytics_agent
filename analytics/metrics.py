"""
AI Analytics Agent — Metrics Calculator
Computes financial, production, and composite metrics from transformed data.
"""

import logging
from typing import Dict, List

import numpy as np
import pandas as pd

from models.schemas import (
    ProjectMetrics, StackMetrics, TaskTypeMetrics,
    DeveloperMetrics, DashboardSummary,
)

logger = logging.getLogger(__name__)


def build_project_metrics(project_metrics_df: pd.DataFrame) -> List[ProjectMetrics]:
    """Convert project_metrics DataFrame to list of Pydantic models."""
    results = []
    for _, row in project_metrics_df.iterrows():
        results.append(ProjectMetrics(
            project_id=int(row["id"]),
            project_name=row["name"],
            stack=row.get("stack"),
            total_revenue=float(row.get("total_revenue", 0)),
            total_costs=float(row.get("total_costs", 0)),
            profit=float(row.get("total_profit", 0)),
            margin=round(float(row.get("margin", 0)), 2),
            burn_rate=round(float(row.get("burn_rate", 0)), 2),
            revenue_per_hour=round(float(row.get("revenue_per_hour", 0)), 2),
            total_hours=float(row.get("total_actual_hours", 0)),
            status=row.get("profitability_status", "green"),
        ))
    return sorted(results, key=lambda x: x.margin)


def build_stack_metrics(stack_metrics_df: pd.DataFrame) -> List[StackMetrics]:
    """Convert stack_metrics DataFrame to list of Pydantic models."""
    results = []
    for _, row in stack_metrics_df.iterrows():
        results.append(StackMetrics(
            stack=row["stack"],
            project_count=int(row.get("project_count", 0)),
            total_revenue=float(row.get("total_revenue", 0)),
            total_costs=float(row.get("total_costs", 0)),
            profit=float(row.get("total_profit", 0)),
            margin=round(float(row.get("margin", 0)), 2),
            avg_revenue_per_hour=round(float(row.get("avg_revenue_per_hour", 0)), 2),
            total_hours=float(row.get("total_hours", 0)),
            status=row.get("status", "green"),
        ))
    return sorted(results, key=lambda x: x.margin)


def build_task_type_metrics(task_type_df: pd.DataFrame) -> List[TaskTypeMetrics]:
    """Convert task_type_metrics DataFrame to list of Pydantic models."""
    results = []
    for _, row in task_type_df.iterrows():
        results.append(TaskTypeMetrics(
            task_type=row["task_type"],
            task_count=int(row.get("task_count", 0)),
            total_estimated_hours=float(row.get("total_estimated_hours", 0)),
            total_actual_hours=float(row.get("total_actual_hours", 0)),
            overtime_ratio=round(float(row.get("overtime_ratio", 0)), 2),
            total_cost=round(float(row.get("total_cost", 0)), 2),
            reopen_rate=round(float(row.get("reopen_rate", 0)), 2),
            status=row.get("status", "green"),
        ))
    return results


def build_developer_metrics(dev_df: pd.DataFrame) -> List[DeveloperMetrics]:
    """Convert developer_metrics DataFrame to list of Pydantic models."""
    results = []
    for _, row in dev_df.iterrows():
        results.append(DeveloperMetrics(
            developer_id=int(row["id"]),
            developer_name=row["name"],
            role=row.get("role"),
            stack=row.get("stack"),
            total_hours=float(row.get("total_actual", 0)),
            total_cost=round(float(row.get("total_cost", 0)), 2),
            tasks_completed=int(row.get("tasks_completed", 0)),
            avg_estimation_accuracy=round(float(row.get("estimation_accuracy", 0)), 2),
            overtime_ratio=round(float(row.get("overtime_ratio", 0)), 2),
            velocity=round(float(row.get("velocity", 0)), 2),
            efficiency_score=round(float(row.get("efficiency_score", 0)), 2),
        ))
    return sorted(results, key=lambda x: x.efficiency_score)


def build_dashboard_summary(data: Dict[str, pd.DataFrame]) -> DashboardSummary:
    """Build the top-level dashboard summary from all metrics."""
    pm = data.get("project_metrics", pd.DataFrame())
    fin = data.get("financials", pd.DataFrame())

    total_revenue = float(fin["revenue"].sum()) if "revenue" in fin.columns else 0
    total_costs = float(fin["costs"].sum()) if "costs" in fin.columns else 0
    total_profit = total_revenue - total_costs
    overall_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

    projects = build_project_metrics(pm) if len(pm) > 0 else []
    stacks = build_stack_metrics(data.get("stack_metrics", pd.DataFrame()))
    task_types = build_task_type_metrics(data.get("task_type_metrics", pd.DataFrame()))

    loss_count = sum(1 for p in projects if p.status == "red")

    return DashboardSummary(
        total_revenue=round(total_revenue, 2),
        total_costs=round(total_costs, 2),
        total_profit=round(total_profit, 2),
        overall_margin=round(overall_margin, 2),
        project_count=len(data.get("projects", pd.DataFrame())),
        developer_count=len(data.get("developers", pd.DataFrame())),
        task_count=len(data.get("tasks", pd.DataFrame())),
        loss_projects_count=loss_count,
        projects=projects,
        stacks=stacks,
        task_types=task_types,
    )
