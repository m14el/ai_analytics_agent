"""
AI Analytics Agent — Database Models
SQLAlchemy ORM models for analytical storage.
"""

from datetime import datetime, date, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Text, Boolean,
    ForeignKey, create_engine, Enum as SAEnum,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from config import settings

Base = declarative_base()


# ── Projects ────────────────────────────────────────────────
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    project_type = Column(String(100))       # web, mobile, game, etc.
    client = Column(String(255))
    stack = Column(String(100))              # Unity, UE, Flutter, Vue.js, etc.
    status = Column(String(50), default="active")  # active, completed, paused
    start_date = Column(Date)
    end_date = Column(Date)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    financials = relationship("Financial", back_populates="project")
    tasks = relationship("Task", back_populates="project")
    developer_assignments = relationship("DeveloperAssignment", back_populates="project")


# ── Developers ──────────────────────────────────────────────
class Developer(Base):
    __tablename__ = "developers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    role = Column(String(100))               # junior, middle, senior, lead
    stack = Column(String(100))
    hourly_rate = Column(Float, default=0.0)  # USD/hour
    monthly_salary = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    tasks = relationship("Task", back_populates="developer")
    assignments = relationship("DeveloperAssignment", back_populates="developer")


# ── Developer ↔ Project assignment ─────────────────────────
class DeveloperAssignment(Base):
    __tablename__ = "developer_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    developer_id = Column(Integer, ForeignKey("developers.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    hours_allocated = Column(Float, default=0.0)
    hours_actual = Column(Float, default=0.0)
    period_start = Column(Date)
    period_end = Column(Date)

    developer = relationship("Developer", back_populates="assignments")
    project = relationship("Project", back_populates="developer_assignments")


# ── Tasks (AppTask equivalent) ──────────────────────────────
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(100))        # ID from AppTask
    title = Column(String(500), nullable=False)
    description = Column(Text)
    task_type = Column(String(100))          # feature, bug, improvement, etc.
    status = Column(String(50))              # open, in_progress, done, closed
    priority = Column(String(50))            # low, medium, high, critical
    project_id = Column(Integer, ForeignKey("projects.id"))
    developer_id = Column(Integer, ForeignKey("developers.id"))
    estimated_hours = Column(Float, default=0.0)
    actual_hours = Column(Float, default=0.0)
    reopen_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    created_date = Column(Date)
    completed_date = Column(Date)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="tasks")
    developer = relationship("Developer", back_populates="tasks")


# ── Financials ──────────────────────────────────────────────
class Financial(Base):
    __tablename__ = "financials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    period = Column(Date, nullable=False)     # monthly period
    revenue = Column(Float, default=0.0)
    costs = Column(Float, default=0.0)        # total costs
    labor_costs = Column(Float, default=0.0)  # developer salaries
    overhead_costs = Column(Float, default=0.0)  # infrastructure, licenses, etc.
    profit = Column(Float, default=0.0)
    margin = Column(Float, default=0.0)       # profit / revenue * 100
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="financials")


# ── Analytics Snapshot (aggregated results) ─────────────────
class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    snapshot_type = Column(String(50))        # daily, weekly, monthly
    data_json = Column(Text)                  # JSON blob with aggregated metrics
    ai_analysis = Column(Text)                # AI-generated analysis text
    ai_hypotheses = Column(Text)              # AI-generated hypotheses
    ai_recommendations = Column(Text)         # AI-generated recommendations
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ── Engine & Session ────────────────────────────────────────
engine = create_engine(settings.analytics_db_url, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    """Create all tables in the analytical database."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
