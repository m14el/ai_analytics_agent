"""
AI Analytics Agent — Dashboard Routes
FastAPI routes for the web dashboard and API endpoints.
"""
import json
import logging
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from etl.extract import get_extractor
from etl.transform import transform
from etl.load import load
from analytics.metrics import build_dashboard_summary, build_developer_metrics
from analytics.anomaly import detect_all_anomalies
from analytics.ai_engine import run_analysis

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# In-memory cache for the latest analytics data
_cache: Dict = {}


def _to_dicts(pydantic_list):
    """Convert a list of Pydantic models to a list of plain dicts (JSON-safe)."""
    if not pydantic_list:
        return []
    return [item.model_dump() if hasattr(item, "model_dump") else item for item in pydantic_list]


def _summary_to_dict(summary):
    """Convert DashboardSummary to a fully JSON-serializable dict for templates."""
    if summary is None:
        return {}
    d = summary.model_dump()
    # Ensure datetime in ai_analysis is string
    if d.get("ai_analysis") and d["ai_analysis"].get("generated_at"):
        d["ai_analysis"]["generated_at"] = str(d["ai_analysis"]["generated_at"])
    return d


async def run_etl_pipeline() -> Dict:
    """Run the full ETL + analysis pipeline and cache results."""
    global _cache
    logger.info("=" * 60)
    logger.info("Running ETL pipeline...")

    extractor = get_extractor()
    raw_data = extractor.extract_all()
    transformed = transform(raw_data)

    load(transformed)

    anomalies = detect_all_anomalies(transformed)
    summary = build_dashboard_summary(transformed)
    dev_metrics = build_developer_metrics(
        transformed.get("developer_metrics", __import__("pandas").DataFrame())
    )

    ai_result = await run_analysis(transformed, anomalies)
    summary.ai_analysis = ai_result

    _cache = {
        "summary": summary,
        "summary_dict": _summary_to_dict(summary),
        "developer_metrics": dev_metrics,
        "developer_metrics_dicts": _to_dicts(dev_metrics),
        "anomalies": anomalies,
        "transformed": transformed,
    }
    logger.info("ETL pipeline completed successfully")
    logger.info("=" * 60)
    return _cache


# ── HTML Pages ──────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    if not _cache:
        await run_etl_pipeline()
    sd = _cache.get("summary_dict", {})
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "summary": sd,
        "anomalies": _cache.get("anomalies", []),
    })


@router.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request):
    if not _cache:
        await run_etl_pipeline()
    sd = _cache.get("summary_dict", {})
    return templates.TemplateResponse("projects.html", {
        "request": request,
        "projects": sd.get("projects", []),
    })


@router.get("/stacks", response_class=HTMLResponse)
async def stacks_page(request: Request):
    if not _cache:
        await run_etl_pipeline()
    sd = _cache.get("summary_dict", {})
    return templates.TemplateResponse("stacks.html", {
        "request": request,
        "stacks": sd.get("stacks", []),
    })


@router.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    if not _cache:
        await run_etl_pipeline()
    sd = _cache.get("summary_dict", {})
    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "task_types": sd.get("task_types", []),
        "anomalies": [a for a in _cache.get("anomalies", []) if a["type"].startswith("task_")],
    })


@router.get("/developers", response_class=HTMLResponse)
async def developers_page(request: Request):
    if not _cache:
        await run_etl_pipeline()
    return templates.TemplateResponse("developers.html", {
        "request": request,
        "developers": _cache.get("developer_metrics_dicts", []),
    })


# ── API Endpoints ───────────────────────────────────────────

@router.get("/api/summary")
async def api_summary():
    if not _cache:
        await run_etl_pipeline()
    return _cache.get("summary")


@router.get("/api/anomalies")
async def api_anomalies():
    if not _cache:
        await run_etl_pipeline()
    return _cache.get("anomalies", [])


@router.get("/api/ai-analysis")
async def api_ai_analysis():
    if not _cache:
        await run_etl_pipeline()
    s = _cache.get("summary")
    return s.ai_analysis if s else {}


@router.post("/api/etl/run")
async def api_run_etl():
    result = await run_etl_pipeline()
    return {"status": "ok", "projects": len(result["summary"].projects)}
