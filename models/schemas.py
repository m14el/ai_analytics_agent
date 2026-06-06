"""
AI Analytics Agent — Pydantic Schemas
Request/response validation schemas for the API.
"""

from datetime import date, datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field


# ── Project Schemas ─────────────────────────────────────────
class ProjectBase(BaseModel):
    name: str
    project_type: Optional[str] = None
    client: Optional[str] = None
    stack: Optional[str] = None
    status: str = "active"
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectOut(ProjectBase):
    id: int
    revenue: float = 0.0
    costs: float = 0.0
    profit: float = 0.0
    margin: float = 0.0
    profitability_status: str = "green"  # green / yellow / red

    class Config:
        from_attributes = True


# ── Developer Schemas ───────────────────────────────────────
class DeveloperBase(BaseModel):
    name: str
    role: Optional[str] = None
    stack: Optional[str] = None
    hourly_rate: float = 0.0
    monthly_salary: float = 0.0


class DeveloperOut(DeveloperBase):
    id: int
    total_hours: float = 0.0
    total_cost: float = 0.0
    efficiency: float = 0.0

    class Config:
        from_attributes = True


# ── Task Schemas ────────────────────────────────────────────
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    task_type: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    estimated_hours: float = 0.0
    actual_hours: float = 0.0


class TaskOut(TaskBase):
    id: int
    project_name: Optional[str] = None
    developer_name: Optional[str] = None
    reopen_count: int = 0
    comments_count: int = 0
    overtime_ratio: float = 0.0  # actual / estimated
    cost: float = 0.0

    class Config:
        from_attributes = True


# ── Financial Schemas ───────────────────────────────────────
class FinancialOut(BaseModel):
    id: int
    project_name: Optional[str] = None
    period: date
    revenue: float = 0.0
    costs: float = 0.0
    labor_costs: float = 0.0
    overhead_costs: float = 0.0
    profit: float = 0.0
    margin: float = 0.0

    class Config:
        from_attributes = True


# ── Analytics / Metrics ─────────────────────────────────────
class ProjectMetrics(BaseModel):
    """Aggregated profitability metrics for a single project."""
    project_id: int
    project_name: str
    stack: Optional[str] = None
    total_revenue: float = 0.0
    total_costs: float = 0.0
    profit: float = 0.0
    margin: float = 0.0
    burn_rate: float = 0.0
    revenue_per_hour: float = 0.0
    total_hours: float = 0.0
    status: str = "green"  # green / yellow / red


class StackMetrics(BaseModel):
    """Aggregated profitability metrics for a technology stack."""
    stack: str
    project_count: int = 0
    total_revenue: float = 0.0
    total_costs: float = 0.0
    profit: float = 0.0
    margin: float = 0.0
    avg_revenue_per_hour: float = 0.0
    total_hours: float = 0.0
    status: str = "green"


class TaskTypeMetrics(BaseModel):
    """Metrics grouped by task type."""
    task_type: str
    task_count: int = 0
    total_estimated_hours: float = 0.0
    total_actual_hours: float = 0.0
    overtime_ratio: float = 0.0
    total_cost: float = 0.0
    reopen_rate: float = 0.0
    status: str = "green"


class DeveloperMetrics(BaseModel):
    """Efficiency metrics for a developer."""
    developer_id: int
    developer_name: str
    role: Optional[str] = None
    stack: Optional[str] = None
    total_hours: float = 0.0
    total_cost: float = 0.0
    tasks_completed: int = 0
    avg_estimation_accuracy: float = 0.0
    overtime_ratio: float = 0.0
    velocity: float = 0.0
    efficiency_score: float = 0.0


# ── AI Analysis ─────────────────────────────────────────────
class AIHypothesis(BaseModel):
    """A single AI-generated hypothesis."""
    title: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence 0-1")
    affected_metrics: List[str] = []
    source_data: List[str] = []
    severity: str = "medium"  # low / medium / high / critical


class AIRecommendation(BaseModel):
    """A single AI-generated recommendation."""
    category: str  # process, stack, management
    title: str
    description: str
    expected_impact: str
    affected_metrics: List[str] = []
    priority: str = "medium"


class AIAnalysisResult(BaseModel):
    """Complete AI analysis output."""
    summary: str
    hypotheses: List[AIHypothesis] = []
    recommendations: List[AIRecommendation] = []
    anomalies: List[dict] = []
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Dashboard Summary ──────────────────────────────────────
class DashboardSummary(BaseModel):
    """Top-level dashboard data."""
    total_revenue: float = 0.0
    total_costs: float = 0.0
    total_profit: float = 0.0
    overall_margin: float = 0.0
    project_count: int = 0
    developer_count: int = 0
    task_count: int = 0
    loss_projects_count: int = 0
    projects: List[ProjectMetrics] = []
    stacks: List[StackMetrics] = []
    task_types: List[TaskTypeMetrics] = []
    ai_analysis: Optional[AIAnalysisResult] = None
